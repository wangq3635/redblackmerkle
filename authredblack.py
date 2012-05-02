from collections import namedtuple
import json

"""
An authenticated search structure [1] using Okasaki-style red-black trees [2].

[1] http://cs.brown.edu/people/aris/pubs/pad.pdf
[2] http://www.eecs.usma.edu/webs/people/okasaki/jfp99.ps

"""

def AuthRedBlack(H = lambda _: '', k=64):
    """
    Returns:
        dict with functions
    """    
    def digest(D):
        # The hash corresponding to a node is the Hash function applied
        # to the concatenation its children's hashes and its own value
        if not D: return ''
        c, _, (k, dL, dR), _ = D
        return H((c, k, dL, dR))


    def rehash(D):
        # Recompute the hashes for each node, but only if the children
        # are available. Otherwise, we assume the current value is correct.
        c, L, (k, dL, dR), R = D
        if L: dL = digest(L)
        if R: dR = digest(R)
        return (c, L, (k, dL, dR), R)


    def balance(D):
        # This is the simplest way I could think of simulating the 
        # pattern matching from Haskell. The point is to be able to
        # use the very elegant statement from the Okasaki paper [1]
        # (see the return statement in this function)
        # TODO: find a more elegant way to write this
        R,B,a,b,c,d,x,y,z,m,n,o,p,_ = 'RBabcdxyzmnop_'
        def match(*args):
            table = {}
            def _match(left,right):
                if left in ('R','B'): return left == right
                if isinstance(left, tuple):
                    return len(right) == len(left) and \
                        all((_match(*pair) for pair in zip(left, right)))
                assert left in 'abcdxyzmnop_'
                table[left] = right
                return True

            if _match(args, D):
                a,b,c,d,x,y,z,m,n,o,p = map(table.get, 'abcdxyzmnop')
                return (R,(B,a,(x,m,n),b),(y,'',''),(B,c,(z,o,p),d))
            else: return None

        return rehash(match(B,(R,(R,a,(x,m,n),b),(y,_,o),c),(z,_,p),d) or
                      match(B,(R,a,(x,m,_),(R,b,(y,n,o),c)),(z,_,p),d) or
                      match(B,a,(x,m,_),(R,(R,b,(y,n,o),c),(z,_,p),d)) or
                      match(B,a,(x,m,_),(R,b,(y,n,_),(R,c,(z,o,p),d))) or
                      D)


    def search(q, D):
        """
        Returns:
            An interator of elements forming a proof object for a search
        """
        if not D: raise StopIteration
        c, left, (k, dL, dR), right = D
        yield c, (k, dL, dR)

        child = left if q <= k else right # Inner node
        for c,kh in search(q, child):
            yield c,kh


    def query(q, D):
        proof = tuple(search(q, D))
        if not proof: return None, proof
        (c,(k, _, _)) = proof[-1]
        return k == q, proof


    def verify(q, d0, proof):
        proof = tuple(proof)
        r = reconstruct(iter(proof))
        assert digest(r) == d0
        assert proof == tuple(search(q, r))
        return True


    def reconstruct(proof):
        """
        Reconstruct a partial view of a tree (a path from root to leaf)
        given a proof object consisting of the colors and values from
        the path.

        Invariant:
            forall q and D:
            search(1, reconstruct(search(q, D))) == search(q, D)
        """
        try:
            c,(k,hL,hR) = proof.next()
        except StopIteration:
            return ()

        child = reconstruct(proof)
        if not child:
            assert hL == hR == ''
            return (c, (), (k, hL, hR), ())

        else:
            _, _, (_k, _, _), _R = child
            if _k <= k:
                assert hL == digest(child)
                return (c, child, (k, hL, hR), ())
            else:
                assert hR == digest(child)
                return (c, (), (k, hL, hR), child)                    


    def insert(q, D):
        """
        Insert element x into the tree.
        Exceptions:
            AssertionError if x is already in the tree.
        """
        x = (q, '', '')

        def ins(D):
            # Trivial case
            if not D: return ('B', (), x, ())

            # Element already exists (insert is idempotent)
            c, a, y, b = D
            if q == y[0]: return D

            # Leaf node found (this will become the parent)
            if q < y[0] and not a:
                return balance(rehash(('R', ins(a), x, make_black(D))))

            if q > y[0] and not b: 
                return balance(rehash(('R', make_black(D), y, ins(b))))

            # Otherwise recurse
            if q < y[0]: return balance((c, ins(a), y, b))
            if q > y[0]: return balance((c, a, y, ins(b)))

        def make_black(D):
            (c, a, y, b) = D
            return ('B', a, y, b)

        return rehash(make_black(ins(D)))


    def delete(q, D):
        """
        """
        raise NotImplemented

    return locals()