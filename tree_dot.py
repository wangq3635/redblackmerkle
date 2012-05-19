import subprocess
import unittest
import random
from Crypto.Hash import SHA256
import json
import redblack; reload(redblack)
from redblack import SelectRedBlack

H = lambda x: '' if not x else SHA256.new(json.dumps(x)).hexdigest()[:4]
#H = hash
RB = SelectRedBlack(H)
digest = RB.digest
insert = RB.insert
delete = RB.delete
record = RB.record
replay = RB.replay

def tree2dot(D):
    layer = """
digraph BST {
node [fontname="Arial"];

%s
}
    """
    dO = digest(())

    def edges(D, level=0):
        if not D: return
        h = lambda x: abs(hash(x))

        (c, L, (k, dL, dR), R) = D

        node = 'N%d_%s' % (level, h(k))
        color, shape = (('red','ellipse') if c == 'R' else 
                        ('black', 'ellipse'))
        if dL == dR == dO:
            yield '%s [label="(%d) %s: %s", color=%s, shape=%s]\n' % \
                (node, digest(D)[0], k[0], k[1], color, shape)
        else:
            yield '%s [label="(%d) %s || %s || %s", color=%s, shape=%s]\n' % \
                (node, digest(D)[0], dL[1], k[0], dR[1], color, shape)

        for dX,X,label in ((dL,L,'L'),(dR,R,'R')):
            if X: yield '%s -> N%d_%s;\n' % (node, level+1, h(X[2][0]))
            elif dX[0]:
                n = 'null_%d_%s_%s' % (level+1, h(k), label)
                yield '%s -> %s;\n' % (node, n)
                yield '%s [shape=point, label=x];\n' % (n)

        for s in edges(L, level+1): yield s
        for s in edges(R, level+1): yield s

    return layer % (''.join(edges(D)))
    


def dot2png(dot):
    from subprocess import PIPE
    P = subprocess.Popen('dot -Tpng'.split(), 
                         stdout=PIPE, stdin=PIPE, stderr=PIPE)
    stdout, stderr = P.communicate(dot)
    #print dot
    if stderr: print stderr
    return stdout


def tree2png(filename, D):
    open(filename, 'w').write(dot2png(tree2dot(D)))


def reconstruct(d0, VO):
    d = dict((RB.H(C), C) for C in VO)
    def _recons(d0):
        if not d0 in d: return ()
        (c, dL, k, dR) = d[d0]
        return (c, _recons(dL), (k, dL, dR), _recons(dR))
    return _recons(d0)

aplus = lambda x: chr(ord('a')+x)

D = ()
for i in (5,3,7,9,11):
    D = insert(i, D, aplus(i))
    tree2png('dots/test_reconstruct_i%d.png'%i, D)

d0 = digest(D)
tree2png('dots/test_reconstruct_0.png', D)
T = record(D); T.insert(10); R = reconstruct(d0, T.VO)
tree2png('dots/test_reconstruct_r0.png', R)
tree2png('dots/test_reconstruct_1.png', insert(10, D, aplus(10)))
tree2png('dots/test_reconstruct_r1.png', insert(10, R, aplus(10)))

D = ()
values = range(31)
#random.shuffle(values)
for v in values: D = insert(v, D, aplus(v))
tree2png('dots/sequential.png', D)
D = insert(len(values)+0, D)
tree2png('dots/sequential_31.png', D)


D = ()
values = range(16)
for i in values:
    D = insert(i, D, aplus(i))
d0 = digest(D)
T = record(D); T.delete(10); R = reconstruct(d0, T.VO)
tree2png('dots/test_delete_0.png', D)
tree2png('dots/test_delete_r0.png', R)
tree2png('dots/test_delete_1.png', delete(10, D))
tree2png('dots/test_delete_r1.png', delete(10, R))


def test_delete(n=100):
    for _ in range(n):
        D = ()
        values = range(16)
        random.shuffle(values)
        for i in values: D = insert(i, D)
        random.shuffle(values)
        for i in values[:4]:
            S = delete(i, D)
            T = record(D); T.delete(i)
            R = reconstruct(digest(D), T.VO)
            SR = delete(i, R)
            try:
                assert digest(SR) == digest(S)
            except:
                tree2png('dots/delete_10_0.png', D)
                tree2png('dots/delete_10_1.png', S)
                tree2png('dots/delete_10_r0.png', R)
                tree2png('dots/delete_10_r1.png', SR)
                raise
            D = S

test_delete()
