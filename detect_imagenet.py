#!/usr/bin/env python3
import sys, os, json, argparse
from urllib.parse import urlsplit
from urllib.request import urlopen, Request
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50
from PIL import Image

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
        model = resnet50(pretrained=True)
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

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('image')
    p.add_argument('-k', '--topk', type=int, default=10)
    p.add_argument('-i', '--id', action='store_true')
    args = p.parse_args()
    clsprobs = detect(args.image, args.topk)
    for cls, id, prob in clsprobs:
        if args.id:
            print(f'{cls} ({id}):\t{prob:.2%}')
        else:
            print(f'{cls}:\t{prob:.2%}')
