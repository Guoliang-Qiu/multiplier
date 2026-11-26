from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0007/trial_b.py')
s=p.read_text()
# Keep the parent's deliberate AND/OR XOR decomposition for sharing.
pos=s.index('    def _product_columns_before_compensation_previous(self,')
s=s[:pos]+'''    def _product_columns(self, a, b, c, d, zero, one):
        """Fuse the second parent's G slot edits using semantic graph references.

        The OR at column 3 is split into its two constituent Boolean terms;
        their order matters to the approximate column-3 compressor.
        """
        cols = self._product_columns_before_compensation(a, b, c, d, zero, one)
        # Two constant ones compress to the same column-3 carry as the
        # original [zero,one,zero,one] but require two fewer column slots.
        cols[2] = [zero, one, zero, one]
        first, second = self.nodes[cols[3][2]].inputs
        cols[3] = [cols[3][0], first]
        old4 = cols[4]
        cols[4] = [old4[2], old4[4], old4[0], old4[3], one]
        return cols


def build_circuit():
    return Candidate()._build_circuit()
'''
p.write_text(s)
