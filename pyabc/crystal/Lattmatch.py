import math
import numpy as np

from pyabc.crystal.structure import Cell
from pyabc.io.vasp import  *
from pyabc.crystal.utils import non_dup_hnfs, _is_hnf_dup, _hnfs
from numpy.linalg import  *
from itertools import combinations





def match(pcell_A, pcell_B, n_max, distance, err_l, err_s, err_theta):

    s_A =  abs(det(np.array(pcell_A._lattice[0:2, 0:2])))
    s_B =  abs(det(np.array(pcell_B._lattice[0:2, 0:2])))
    nms = []

    for n in range(1, n_max+1):
        for m in range(math.floor(s_A/s_B), math.floor(n_max*s_A/s_B)+1):
            if abs(n*s_A-m*s_B) < err_s*n*s_A:
                nms.append([n, m])

    NM = np.array(nms)
    print(NM)
    A_b = []
    B_a = []
    for nm in NM:

        slatt_A = non_dup_hnfs(pcell_A, nm[0], dimension=2)
        slatt_B = non_dup_hnfs(pcell_B, nm[1], dimension=2)
        slatt_A_d = []
        slatt_B_d = []
        for l_A in slatt_A:

            lat = delaunay_reduce_2D(pcell_A._lattice, l_A)
            slatt_A_d.append(lat)


        for l_B in slatt_B:
            lat = delaunay_reduce_2D(pcell_B._lattice, l_B)
            slatt_B_d.append(lat)


        for l_A_d in slatt_A_d:
            dis1_A = math.sqrt(l_A_d[0,0]**2+l_A_d[0,1]**2)
            dis2_A = math.sqrt(l_A_d[1,0]**2+l_A_d[1,1]**2)
            theta_A = (l_A_d[0,0]*l_A_d[1,0]+l_A_d[0,1]*l_A_d[1,1])/dis1_A/dis2_A
            for l_B_d in slatt_B_d:
                dis1_B = math.sqrt(l_B_d[0,0]**2+l_B_d[0,1]**2)
                dis2_B = math.sqrt(l_B_d[1,0]**2+l_B_d[1,1]**2)
                theta_B = (l_B_d[0,0]*l_B_d[1,0]+l_B_d[0,1]*l_B_d[1,1])/dis1_B/dis2_B
                if (abs(dis1_A - dis1_B) < err_l*dis1_A and
                    abs(dis2_A - dis2_B) < err_l*dis2_A and
                    abs(theta_A - theta_B) < err_theta):
                    A_b.append(np.round(l_A_d*np.matrix(pcell_A._lattice).I).astype(int))
                    B_a.append(np.round(l_B_d*np.matrix(pcell_B._lattice).I).astype(int))


    for i in range(0, len(A_b)):

        scell_A = Cell.extend(pcell_A, A_b[i])
        scell_B = Cell.extend(pcell_B, B_a[i])

        latt_layer = scell_A._lattice
        positions_B = scell_B._positions + np.repeat([[0, 0, np.amax(scell_A._positions[:,2])+distance/latt_layer[2,2]]], len(scell_B._atoms), axis=0)
        positions_layer = np.vstack((scell_A._positions,positions_B))
        atoms_layer = list(scell_A._atoms) + list(scell_B._atoms)
        # import pdb; pdb.set_trace()
        cell_layer =  Cell(latt_layer, positions_layer, atoms_layer)
        write(cell_layer, filename='POSCAR'+str(i), suffix='.vasp', long_format=True)

########扩胞和怎么错位



def delaunay_reduce_2D(platt, hnfm):
    ###变换基矢到饱满,算法来自1957<<Remarks on the Delaunay Reduction>>
    latt = np.matrix(hnfm)*np.matrix(platt)
    s = abs(det(np.array(latt)))
    latt_2D = latt[0:2, 0:2]
    a = np.row_stack((latt_2D, -(latt_2D[0]+latt_2D[1])))
    com = list(combinations([0, 1, 2], 2))
    for t in range(1,1000):
        k = 0
        for ij in com:
            hij = a[ij[0]]*a[ij[1]].T
            if hij>0.00001:
                a[0] = -a[ij[0]]
                a[1] = a[ij[1]]
                a[2] = -(a[0]+a[1])
                break
            k += 1
        if k == 3:
            ###三个夹角都是非锐角时,结束
            break
    dis1 = a[0,0]**2+a[0,1]**2
    dis2 = a[1,0]**2+a[1,1]**2
    dis3 = a[2,0]**2+a[2,1]**2
    dis = [dis1, dis2, dis3]
    a_dis = np.column_stack((a, dis))
    b = np.matrix(a_dis[np.lexsort(a_dis.T)])####选取最短两条
    latt[0:2, 0:2] = b[0:2, 0:2]
    if (t < 999 and abs(abs(det(np.array(latt)))-s) < 0.1):
        return latt
    else:
        raise ValueError("This cell can't transform to a full cell.")


bcc_latt = [3.19, 0, 0,
            1.595, 2.7626, 0,
            0, 0, 10]
bcc_pos = [(0, 0, 0.01)]
bcc_atoms = [12]
pcell_A = Cell(bcc_latt, bcc_pos, bcc_atoms)
fcc_latt = [2.929, 0, 0,
            1.4645, 2.537, 0,
            0, 0, 10]
fcc_pos = [(0, 0, 0.01 )]
fcc_atoms = [22]
pcell_B = Cell(fcc_latt, fcc_pos, fcc_atoms)
match(pcell_A, pcell_B, 10, distance=1, err_l = 0.1, err_s = 0.1, err_theta = 0.05)
##distance:吸附层和衬底间距离(挨)
