# -*- coding: utf-8 -*-
"""
Created on Sun Jan 28 18:12:44 2018

@author: Utkarsh
"""

import numpy as np
from skimage.morphology import convex_hull_image, erosion

def getTerminationBifurcation(img, mask):
    
    img = img == 255;
    (rows, cols) = img.shape;
    minutiaeTerm = np.zeros(img.shape);
    minutiaeBif = np.zeros(img.shape);
    
    for i in range(1,rows-1):
        for j in range(1,cols-1):
            if(img[i][j] == 1):
                block = img[i-1:i+2,j-1:j+2];
                block_val = np.sum(block);
                if(block_val == 2):
                    minutiaeTerm[i,j] = 1;
                    
                elif(block_val == 4):
                    minutiaeBif[i,j] = 1;
                    
    mask = convex_hull_image(mask>0)
    mask = erosion(mask, np.ones((5, 5), dtype=bool))         # 5x5 square structuring element for mask erosion
    minutiaeTerm = np.uint8(mask)*minutiaeTerm
    
    return(minutiaeTerm, minutiaeBif)