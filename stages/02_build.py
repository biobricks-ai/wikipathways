import os, sys, zipfile, time
import rdflib
from rdflib import Graph, URIRef, Literal, BNode
import pyarrow as pa
import pyarrow.parquet as pq

# BUILD: parse WikiPathways RDF (TTL) directly into a streaming triples parquet.
# Replaces the former rdf2hdt HDT build (rdf2hdt C++ tool not installed).
# Columns: subject, predicate, object, object_type, datatype, language
# Memory-bounded: each per-pathway TTL is parsed into a small graph, rows are
# buffered and flushed to a single ParquetWriter in batches.

base_path = os.getcwd()
rdf_dir = os.path.join(base_path, "download", "01_download", "rdf")
brick_dir = os.path.join(base_path, "brick")
os.makedirs(brick_dir, exist_ok=True)

# Remove stale HDT artifacts from the previous (broken) build
for stale in ("wikipathways.hdt", "wikipathways.hdt.index.v1-1"):
    p = os.path.join(brick_dir, stale)
    if os.path.exists(p):
        os.remove(p)

out_path = os.path.join(brick_dir, "wikipathways.parquet")

SCHEMA = pa.schema([
    ("subject", pa.string()),
    ("predicate", pa.string()),
    ("object", pa.string()),
    ("object_type", pa.string()),   # uri | literal | bnode
    ("datatype", pa.string()),
    ("language", pa.string()),
])

zip_specs = [
    ("wikipathways-20240610-rdf-wp.zip", "wp"),
    ("wikipathways-20240610-rdf-gpml.zip", "gpml"),
    ("wikipathways-20240610-rdf-authors.zip", "authors"),
]

BATCH = 500_000
writer = pq.ParquetWriter(out_path, SCHEMA, compression="zstd")

buf_s, buf_p, buf_o, buf_ot, buf_dt, buf_lang = [], [], [], [], [], []
total = 0
n_files = 0


def flush():
    global buf_s, buf_p, buf_o, buf_ot, buf_dt, buf_lang
    if not buf_s:
        return
    tbl = pa.table({
        "subject": pa.array(buf_s, type=pa.string()),
        "predicate": pa.array(buf_p, type=pa.string()),
        "object": pa.array(buf_o, type=pa.string()),
        "object_type": pa.array(buf_ot, type=pa.string()),
        "datatype": pa.array(buf_dt, type=pa.string()),
        "language": pa.array(buf_lang, type=pa.string()),
    }, schema=SCHEMA)
    writer.write_table(tbl)
    buf_s, buf_p, buf_o, buf_ot, buf_dt, buf_lang = [], [], [], [], [], []


def term_str(t, bnode_prefix):
    # Return (value, type, datatype, language)
    if isinstance(t, URIRef):
        return str(t), "uri", None, None
    if isinstance(t, BNode):
        # namespace blank nodes per source file to avoid cross-file id collisions
        return f"_:{bnode_prefix}_{str(t)}", "bnode", None, None
    if isinstance(t, Literal):
        dt = str(t.datatype) if t.datatype is not None else None
        lang = t.language if t.language else None
        return str(t), "literal", dt, lang
    return str(t), "literal", None, None


t0 = time.time()
for zname, kind in zip_specs:
    zpath = os.path.join(rdf_dir, zname)
    if not os.path.exists(zpath):
        print(f"WARN missing {zpath}, skipping", flush=True)
        continue
    with zipfile.ZipFile(zpath) as zf:
        names = [n for n in zf.namelist() if n.endswith(".ttl")]
        print(f"{kind}: {len(names)} ttl files", flush=True)
        for i, name in enumerate(names):
            data = zf.read(name)
            stem = os.path.splitext(os.path.basename(name))[0]
            bnode_prefix = f"{kind}_{stem}"
            g = Graph()
            try:
                g.parse(data=data, format="turtle")
            except Exception as e:
                print(f"WARN parse fail {name}: {e}", flush=True)
                continue
            for s, p, o in g:
                sv, _, _, _ = term_str(s, bnode_prefix)
                pv = str(p)
                ov, ot, dt, lang = term_str(o, bnode_prefix)
                buf_s.append(sv)
                buf_p.append(pv)
                buf_o.append(ov)
                buf_ot.append(ot)
                buf_dt.append(dt)
                buf_lang.append(lang)
                total += 1
            n_files += 1
            if len(buf_s) >= BATCH:
                flush()
            if (i + 1) % 500 == 0:
                print(f"  {kind} {i+1}/{len(names)} files, {total} triples, "
                      f"{round(time.time()-t0)}s", flush=True)

flush()
writer.close()
print(f"DONE: {total} triples from {n_files} files -> {out_path} "
      f"({round(time.time()-t0)}s)", flush=True)
print(f"parquet size: {os.path.getsize(out_path)} bytes", flush=True)
