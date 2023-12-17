#!/usr/bin/env python3
import sys, os, json, argparse, warnings
from urllib.parse import urlsplit
from urllib.request import urlopen, Request
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image
from nltk.corpus import wordnet

USER_AGENT = 'dummy_user_agent'

DIR = os.path.dirname(__file__)
CLASS_INDEX_FILE = os.path.join(DIR, 'data', 'imagenet_class_index.json')

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

model = None
classes = None

def detect(image, k=10):
    global model, classes
    if isinstance(image, str):
        if len(urlsplit(image).scheme) > 1:
            image = urlopen(Request(image, headers={'User-Agent': USER_AGENT}))
        image = Image.open(image).convert('RGB')

    if model is None:
        model = resnet50(weights=ResNet50_Weights.DEFAULT)
        model.eval()

    if classes is None:
        with open(CLASS_INDEX_FILE) as classfile:
            classes = json.load(classfile)
            classes = {int(i): (cls, id) for i, (id, cls) in classes.items()}

    image = preprocess(image)
    scores = model(image.unsqueeze(0)).squeeze(0).log_softmax(0)
    topscore, topind = scores.topk(k)
    topprob = topscore.exp()
    clsprobs = [(*classes[i], prob) for i, prob in
                zip(topind.tolist(), topprob.tolist())]
    return clsprobs

def in_hypernym_closure(synset, target):
    with warnings.catch_warnings(action='ignore'):
        return (synset == target or
                target in synset.closure(lambda s: s.hypernyms()))

def detect_synset(image, synset, k=1):
    if '.' in synset:
        target = wordnet.synset(synset)
    else:
        target = wordnet.synsets(synset, pos=wordnet.NOUN)[0]
    detections = detect(image, k)
    match = False
    tot_prob = 0
    for cls, id, prob in detections:
        ss = wordnet.synset_from_pos_and_offset(id[0], int(id[1:]))
        if in_hypernym_closure(ss, target):
            match = True
            tot_prob += prob
    return match, tot_prob

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('image', nargs='+')
    p.add_argument('-s', '--synset', default='bird.n.01')
    p.add_argument('-k', '--topk', type=int, default=1)
    p.add_argument('-p', '--prob', action='store_true')
    args = p.parse_args()
    for image in args.image:
        match, prob = detect_synset(image, args.synset, args.topk)
        if match:
            print(f'Yes: {prob:%}' if args.prob else 'Yes')
        else:
            print('No')
