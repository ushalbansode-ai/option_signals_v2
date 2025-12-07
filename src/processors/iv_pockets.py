

def find_iv_pockets(df, magnets, neighbor_width=200):
"""Return metadata for each magnet: low IV pocket, iv_skew etc.
magnets: list of strike ints
"""
if df is None or df.empty:
return {}


pockets_meta = {}
for s in magnets:
row = df[df['strike'] == s]
if row.empty:
continue
row = row.iloc[0]
ce_iv = float(row.get('CE_IV', 0) or 0)
pe_iv = float(row.get('PE_IV', 0) or 0)
iv_skew = ce_iv - pe_iv


neighbors = df[(df['strike'] >= s - neighbor_width) & (df['strike'] <= s + neighbor_width)]
median_iv = 0.0
if not neighbors.empty:
median_iv = neighbors[['CE_IV', 'PE_IV']].median().mean()


is_low_iv_pocket = (ce_iv + pe_iv) < 0.7 * median_iv if median_iv > 0 else False


pockets_meta[int(s)] = {'CE_IV': ce_iv, 'PE_IV': pe_iv, 'iv_skew': iv_skew, 'is_low_iv_pocket': is_low_iv_pocket}


return pockets_meta
