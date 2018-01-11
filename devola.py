#!/usr/bin/python
 
from __future__ import division
import cv2
import sys
import time
import os
import numpy as np
from clint.textui import progress, puts, colored
from optparse import OptionParser
from matplotlib import pyplot as plt
from math import ceil, sqrt
from fractions import gcd
from random import randrange

def inRect(rect, point) :
    if point[0] < rect[0] :
        return False
    elif point[1] < rect[1] :
        return False
    elif point[0] > rect[2] :
        return False
    elif point[1] > rect[3] :
        return False
    return True

def avgRGB(a,b,c):
  return np.average((a,b,c),axis=0)

class InterpolationSet:
#     ======
  data = []                                                    # Initialize list
  colors = []
  subdiv = cv2.Subdiv2D((0, 0, 0, 0))

  def __init__(self,data,w,h):
#     ===================
    self.data = dict(data)
    self.subdiv = cv2.Subdiv2D((0, 0, w, h))

  def save(self):                     # Writes the sampled points in a text file 
#     ==========
    data_list = self.data.items()
    output = open(str(len(data_list)+1) + '_halton.txt', 'w')
    for item in data_list:
      output.write('{} {} {} {} {}\n' \
        .format(item[0][0],item[0][1],item[1][0],item[1][1],item[1][2]))

  def initSubdiv(self):
    with progress.Bar(label=colored.yellow("INIT SUBDIV     "), \
      expected_size=len(self.data)+1) as bar:
      i = 1
      data_list = self.data.items()
      for item in data_list:
        self.subdiv.insert(item[0])
        self.colors.append(item[1])
        i+=1
        bar.show(i)

  def drawVoronoi(self,img):
    (facets, centers) = self.subdiv.getVoronoiFacetList([])
    correspondingCenters = centers.tolist()
    with progress.Bar(label=colored.yellow("INTERPOLATION   "), expected_size=len(facets)+1) as bar:
      for i in xrange(0,len(facets)):
        ifacet_arr = []
        for f in facets[i]:
          ifacet_arr.append(f)
        ifacet = np.array(ifacet_arr, np.int)
        color = self.data[(int(correspondingCenters[i][0]),int(correspondingCenters[i][1]))]
        cv2.fillConvexPoly(img, ifacet, \
          (int(color[0]),int(color[1]),int(color[2])), cv2.LINE_AA, 0);
        cv2.circle(img, (centers[i][0], centers[i][1]), 1, \
          (int(color[0]),int(color[1]),int(color[2])), -1, cv2.LINE_AA, 0)
        bar.show(i+2)

  def drawDelaunay(self,img):
    triangles = self.subdiv.getTriangleList()
    size = img.shape
    r = (0, 0, size[1], size[0])
    for t in triangles:
      pt1 = (int(t[0]), int(t[1]))
      pt2 = (int(t[2]), int(t[3]))
      pt3 = (int(t[4]), int(t[5]))
      if inRect(r, pt1) and inRect(r, pt2) and inRect(r, pt3):
        c = (self.data[pt1],self.data[pt2],self.data[pt3]) 
        poly = np.array([pt1,pt2,pt3], np.int)
        avColor = avgRGB(c[0],c[1],c[2])
        avColor = (int(avColor[0]),int(avColor[1]),int(avColor[2]))
        cv2.fillConvexPoly(img, poly, avColor, cv2.LINE_AA, 0);
        c1 = self.data[pt1]
        c1 = (int(c1[0]),int(c1[1]),int(c1[2]))
        c2 = self.data[pt2]
        c2 = (int(c2[0]),int(c2[1]),int(c2[2]))
        c3 = self.data[pt3]
        c3 = (int(c2[0]),int(c2[1]),int(c2[2]))
        cv2.circle(img, pt1, 3, c1, -1, cv2.LINE_AA, 0)
        cv2.circle(img, pt2, 3, c2, -1, cv2.LINE_AA, 0)
        cv2.circle(img, pt3, 3, c3, -1, cv2.LINE_AA, 0)


class Sampler:
#     =======
  samples = []
  input_name = "image.jpg"
  img = cv2.imread(input_name)
  img_out = np.zeros(img.shape, dtype=img.dtype)
  size = img.shape
  points = InterpolationSet([],size[1], size[0])
  samplesize = (size[1]*size[0])/2


  def __init__(self, s, im, im_out):
#    =============================
    self.samples = []
    self.samplesize = s
    self.input_name = im
    self.img = cv2.imread(im)                           # Create image from name
    self.img_out = np.zeros(self.img.shape, dtype=self.img.dtype)  # Black Image
    size = self.img.shape
    self.points = InterpolationSet([],size[1], size[0])

# Random sampling algorithm using a pseudo-random halton sequence
  def sample(self):
#     ============
    p=2 
    q=3
    seen = set()
    size = self.img.shape
    i = 0
    with progress.Bar(label=colored.yellow("RANDOM SAMPLING "), expected_size=self.samplesize) as bar:
      for i in range(1, self.samplesize):
        fx = 1
        fy = 1
        ix = i
        iy = i
        rx = 0
        ry = 0
    
        while ix > 0:
          fx /= p
          rx += fx * (ix % p)
          ix = ix//p
  
        while iy > 0:
          fy /= q
          ry += fy * (iy % q)
          iy = iy//q
        x = int(rx * size[0])
        y = int(ry * size[1])
        toAppend = ((y,x),(self.img[x,y][0], self.img[x,y][1], self.img[x,y][2]))
        if (toAppend) not in seen:             # Adds calculated point if unique
          seen.add((toAppend))
          self.points.data[(y,x)] = toAppend[1]            # Appends point and color
          self.img_out[x,y] = self.img[x,y]         # Visualize samples in image
          i += 1
        bar.show(i)
    cv2.imwrite(self.input_name + str(self.samplesize)+'_halton.jpg',self.img_out)

  def interpolate(self,out):
#     =====================
    self.points.initSubdiv()
    self.points.drawVoronoi(self.img)
    cv2.imwrite("d.jpg",self.img)
    self.points.drawDelaunay(self.img)
    cv2.imwrite("v.jpg",self.img)

  def __str__(self):
#     =============
    return " Samples: {}\n Input: {}\n Height: {}\n Width: {}\n" \
      .format(self.samplesize, self.input_name, self.img.shape[1], self.img.shape[0])

if __name__ == '__main__':
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)

    parser.add_option("-i", "--input", type="string", dest="input", help="import image to IMG", metavar="IMG_I")
    parser.add_option("-s", "--samples", type="int", dest="samples", help="amount of sampled pixels from IMG", default=1000)
    parser.add_option("-o", "--output", type="string", dest="output", help="export diagram to specified file name", default='out.jpg')
    (options, args) = parser.parse_args()

    if options.input:
      try:
        img = options.input
      except AttributeError:
        puts(colored.red("[ERROR] .jpg file not found in root directory."))
        sys.exit(0)
    if options.output:
      img_out = options.output
    else:
      img_out = "out.jpg"
    if options.samples:
      samples = options.samples
    
    os.system('clear')
    puts("Initializing " + colored.red("DeVola"))
    puts(colored.red("De")+"launay-"+colored.red("Vo")+"ronoi-Sp"+colored.red("la")+"tting")
    sampler = Sampler(samples, img, img_out)
    puts(colored.green("[SUCCESS] Initialized image"))
    print(sampler)
    sampler.sample()
    puts(colored.green("[SUCCESS] Sampled image using halton sampling"))
    sampler.points.save()
    puts(colored.green("[SUCCESS] Saved coordinates in " + \
      colored.blue(str(sampler.samplesize) + "_halton.txt")))
    sampler.interpolate(img_out)
    puts(colored.green("[SUCCESS] Interpolation successfull"))
    puts(colored.green("[SUCCESS] Saved as ") + colored.blue(img_out))