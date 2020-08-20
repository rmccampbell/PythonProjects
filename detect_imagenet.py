#!/usr/bin/env python3
import sys, os, json
from urllib.parse import urlsplit
from urllib.request import urlopen, Request
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50
from PIL import Image

USER_AGENT = 'dummy_user_agent'

DIR = os.path.dirname(__file__)
CLASS_INDEX_FILE = os.path.join(DIR, 'data', 'imagenet_class_index.json')

def detect(image, k=10):
    if isinstance(image, str):
        if len(urlsplit(image).scheme) > 1:
            image = urlopen(Request(image, headers={'User-Agent': USER_AGENT}))
        image = Image.open(image).convert('RGB')

    model = resnet50(pretrained=True)
    model.eval()

    with open(CLASS_INDEX_FILE) as classfile:
        classes = json.load(classfile)
        classes = {int(i): tuple(v[::-1]) for i, v in classes.items()}

    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    image = preprocess(image)

    scores = model(image.unsqueeze(0)).squeeze(0)
    topscore, topind = scores.topk(k)
    topprob = topscore.softmax(0)
    clsprobs = [(*classes[i], p) for i, p in
                zip(topind.tolist(), topprob.tolist())]
    return clsprobs

if __name__ == '__main__':
    clsprobs = detect(*sys.argv[1:])
    for c, p in clsprobs:
        print('{}:\t{}'.format(c, p))
