#!/usr/bin/python
# Filename: histsimilar.py
# -*- coding: utf-8 -*-

from PIL import Image
import os

LEFTFILENOTEXIT = -1
RIGHTFILENOTEXIT = -2

def make_regalur_image(img, size = (256, 256)):
    return img.resize(size).convert('RGB')

def split_image(img, part_size = (64, 64)):
    w, h = img.size
    pw, ph = part_size

    assert w % pw == h % ph == 0

    return [img.crop((i, j, i+pw, j+ph)).copy() \
                for i in xrange(0, w, pw) \
                for j in xrange(0, h, ph)]

def hist_similar(lh, rh):
    assert len(lh) == len(rh)
    return sum(1 - (0 if l == r else float(abs(l - r))/max(l, r)) for l, r in zip(lh, rh))/len(lh)

def calc_similar(li, ri):
#   return hist_similar(li.histogram(), ri.histogram())
    return sum(hist_similar(l.histogram(), r.histogram()) for l, r in zip(split_image(li), split_image(ri))) / 16.0


def calc_similar_by_path(lf, rf):
    if os.path.isfile(lf) is False:
        return LEFTFILENOTEXIT
    if os.path.isfile(rf) is False:
        return RIGHTFILENOTEXIT
    lfSize = os.path.getsize(lf)
    rfSize = os.path.getsize(rf)
    if os.path.isfile(lf) and lfSize > 0 and os.path.isfile(rf) and rfSize > 0:
        li, ri = make_regalur_image(Image.open(lf)), make_regalur_image(Image.open(rf))
        return calc_similar(li, ri)
    elif os.path.isfile(lf) is False:
        return LEFTFILENOTEXIT
    else:
        return RIGHTFILENOTEXIT

def make_doc_data(lf, rf):
    li, ri = make_regalur_image(Image.open(lf)), make_regalur_image(Image.open(rf))
    li.save(lf + '_regalur.png')
    ri.save(rf + '_regalur.png')
    fd = open('stat.csv', 'w')
    fd.write('\n'.join(l + ',' + r for l, r in zip(map(str, li.histogram()), map(str, ri.histogram()))))
#   print >>fd, '\n'
#   fd.write(','.join(map(str, ri.histogram())))
    fd.close()
    import ImageDraw
    li = li.convert('RGB')
    draw = ImageDraw.Draw(li)
    for i in xrange(0, 256, 64):
        draw.line((0, i, 256, i), fill = '#ff0000')
        draw.line((i, 0, i, 256), fill = '#ff0000')
    li.save(lf + '_lines.png')


if __name__ == '__main__':
    path = None
    page1 = '/Users/helen/Project/autoTest/appium-sample/screenShot/63a9bca7/2016-12-15/16:28:46/com.androidesk.livewallpaper/swipeToLeft-2.png'
    page2 = '/Users/helen/Project/autoTest/appium-sample/screenShot/63a9bca7/2016-12-15/16:28:46/com.androidesk.livewallpaper/swipeToLeft-3.png'

    for i in range(4):
        print 'test_case_%d: %.3f%%'%(i, \
            calc_similar_by_path(page1, page2)*100)

#   make_doc_data('test/TEST4/1.JPG', 'test/TEST4/2.JPG')
