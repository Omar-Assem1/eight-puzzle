import json
import multiprocessing
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from puzzle.state import GOAL, is_solvable, random_state

MAX_ANIMATED_STEPS = 400      # longer paths are reported, not animated



def _worker(name, state, conn):
    """Child process: run one algorithm and send back a JSON-friendly dict."""
    from main import run_algorithm

    res = run_algorithm(name, tuple(state))
    animate = res.solved and res.cost <= MAX_ANIMATED_STEPS
    conn.send({
        "solved": res.solved,
        "cost": res.cost,
        "nodes_expanded": res.nodes_expanded,
        "search_depth": res.search_depth,
        "max_depth": res.max_depth,
        "time": res.running_time,
        "path": res.path if animate else None,
        "states": [list(s) for s in res.states] if animate else None,
        "timed_out": False,
    })
    conn.close()


def solve_many(state, algos, timeout):
    jobs = {}
    for name in algos:
        parent_conn, child_conn = multiprocessing.Pipe(duplex=False)
        proc = multiprocessing.Process(target=_worker, args=(name, state, child_conn), daemon=True)
        proc.start()
        child_conn.close()
        jobs[name] = (proc, parent_conn)

    deadline = time.monotonic() + timeout
    results = {}
    for name, (proc, conn) in jobs.items():
        remaining = max(0.0, deadline - time.monotonic())
        if conn.poll(remaining):
            try:
                results[name] = conn.recv()
            except EOFError:             
                results[name] = {"solved": False, "timed_out": False, "error": "worker crashed"}
        else:
            results[name] = {"solved": False, "timed_out": True, "time": timeout}
        if proc.is_alive():
            proc.terminate()
        proc.join(1)
    return results


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):     
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html")
        elif url.path == "/api/random":
            seed = parse_qs(url.query).get("seed", [None])[0]
            state = random_state(int(seed) if seed not in (None, "") else None)
            self._send(200, json.dumps({"state": list(state)}))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if urlparse(self.path).path != "/api/solve":
            return self._send(404, json.dumps({"error": "not found"}))
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            state = tuple(int(x) for x in body["state"])
            if sorted(state) != list(range(9)):
                raise ValueError("state must contain 0..8 exactly once")
            if not is_solvable(state):
                raise ValueError("this board is not solvable (odd number of inversions)")
            from main import ALGORITHMS
            algos = [a for a in body.get("algos", []) if a in ALGORITHMS]
            if not algos:
                raise ValueError("no valid algorithm selected")
            timeout = min(max(float(body.get("timeout", 30)), 1), 300)
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._send(400, json.dumps({"error": str(exc)}))
        self._send(200, json.dumps({"results": solve_many(state, algos, timeout)}))


def serve(port=8080, open_browser=True):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"8-Puzzle GUI running at {url}   (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye!")
    finally:
        server.server_close()

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>8-Puzzle Solver</title>
<style>
:root{
  --bg:#0a0e1a; --bg2:#121833; --card:rgba(255,255,255,.045); --line:rgba(255,255,255,.09);
  --text:#e8ecf8; --muted:#8f99b8; --accent:#7c8cff; --accent2:#38e0c2; --warn:#ffb454; --bad:#ff6b81;
  --tile1:#6d7dff; --tile2:#9a6bff; --ok1:#21d6a8; --ok2:#2aa7d6; --gap:10px;
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  color:var(--text); min-height:100vh;
  background:radial-gradient(1100px 600px at 12% -10%,#222b6b55,transparent 60%),
             radial-gradient(900px 500px at 100% 0%,#0f7d7a33,transparent 60%),
             linear-gradient(180deg,var(--bg),var(--bg2));
}
html{background:#0a0e1a}
.wrap{max-width:1120px;margin:0 auto;padding:28px 20px 48px}
header{display:flex;align-items:center;gap:14px;margin-bottom:24px}
.logo{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-weight:800;
  background:linear-gradient(135deg,var(--tile1),var(--tile2));box-shadow:0 8px 24px #6d7dff55}
h1{font-size:22px;margin:0;letter-spacing:.2px}
header p{margin:2px 0 0;color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:minmax(0,460px) minmax(0,1fr);gap:20px;align-items:start}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px;
  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.card h2{margin:0 0 12px;font-size:12px;letter-spacing:1.4px;text-transform:uppercase;color:var(--muted);font-weight:600}
.stack{display:flex;flex-direction:column;gap:20px}

/* ---- board ---- */
.board{position:relative;width:100%;aspect-ratio:1;border-radius:20px;padding:var(--gap);
  background:linear-gradient(180deg,#0c1126,#0a0e1f);border:1px solid var(--line);
  box-shadow:inset 0 2px 20px #0008}
.slot{position:absolute;left:var(--gap);top:var(--gap);width:calc((100% - 4*var(--gap))/3);aspect-ratio:1;
  border-radius:16px;background:#ffffff08;border:1px dashed #ffffff10;
  transform:translate(calc(var(--c)*(100% + var(--gap))),calc(var(--r)*(100% + var(--gap))))}
.tile{position:absolute;left:var(--gap);top:var(--gap);width:calc((100% - 4*var(--gap))/3);aspect-ratio:1;
  border-radius:16px;display:grid;place-items:center;font-size:clamp(28px,8vw,46px);font-weight:700;color:#fff;
  background:linear-gradient(145deg,var(--tile1),var(--tile2));cursor:pointer;user-select:none;
  box-shadow:0 10px 22px #0006, inset 0 1px 0 #ffffff40;
  transform:translate(calc(var(--c)*(100% + var(--gap))),calc(var(--r)*(100% + var(--gap))));
  transition:transform .3s cubic-bezier(.3,.8,.3,1),background .3s,box-shadow .3s,filter .2s}
.tile:hover{filter:brightness(1.12)}
.tile.ok{background:linear-gradient(145deg,var(--ok1),var(--ok2));box-shadow:0 10px 22px #0006,0 0 0 1px #ffffff30 inset}
.tile.moved{box-shadow:0 0 0 3px #ffffffaa,0 12px 28px #0008}
.board.solved{animation:pulse 1s ease 1}
@keyframes pulse{0%{box-shadow:0 0 0 0 #38e0c288}100%{box-shadow:0 0 0 26px #38e0c200}}

/* ---- transport ---- */
.transport{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:16px}
button,select,input[type=text]{font:inherit;color:var(--text)}
.btn{background:#ffffff0d;border:1px solid var(--line);border-radius:12px;padding:10px 14px;cursor:pointer;
  transition:background .15s,transform .05s,border-color .15s;font-weight:600;font-size:14px}
.btn:hover:not(:disabled){background:#ffffff18;border-color:#ffffff30}
.btn:active:not(:disabled){transform:scale(.97)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn.primary{background:linear-gradient(135deg,var(--tile1),var(--tile2));border-color:transparent;color:#fff;
  box-shadow:0 8px 22px #6d7dff44}
.btn.primary:hover:not(:disabled){filter:brightness(1.1);background:linear-gradient(135deg,var(--tile1),var(--tile2))}
.btn.icon{width:44px;padding:10px 0;text-align:center}
.btn.play{width:56px;height:44px;padding:0}
.scrub{display:flex;align-items:center;gap:12px;margin-top:14px}
input[type=range]{flex:1;accent-color:var(--accent)}
.stepinfo{display:flex;justify-content:space-between;color:var(--muted);font-size:13px;margin-top:8px}
.stepinfo b{color:var(--text)}
.speed{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:12px;margin-top:12px}
.speed input{flex:1}

/* ---- setup ---- */
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input[type=text]{flex:1;min-width:180px;background:#0006;border:1px solid var(--line);border-radius:12px;
  padding:11px 14px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:15px;letter-spacing:1px}
input[type=text]:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px}
input.bad{border-color:var(--bad)}
.hint{font-size:12px;color:var(--muted);margin-top:8px;min-height:16px}
.hint.err{color:var(--bad)}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{border:1px solid var(--line);background:#ffffff08;border-radius:999px;padding:8px 14px;cursor:pointer;
  font-size:13px;font-weight:600;color:var(--muted);transition:all .15s}
.chip:hover{color:var(--text);border-color:#ffffff30}
.chip.on{color:#fff;border-color:transparent;background:linear-gradient(135deg,var(--tile1),var(--tile2));box-shadow:0 6px 18px #6d7dff44}
select{background:#0006;border:1px solid var(--line);border-radius:10px;padding:8px 10px;font-size:13px}
select option{background:#151a36}

/* ---- stats ---- */
.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
@media(max-width:620px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:#0004;border:1px solid var(--line);border-radius:14px;padding:12px}
.stat span{display:block;font-size:11px;color:var(--muted);letter-spacing:.6px;text-transform:uppercase}
.stat b{display:block;margin-top:4px;font-size:20px;font-variant-numeric:tabular-nums}
.status{margin-top:12px;font-size:13px;color:var(--muted)}
.status.good{color:var(--accent2)} .status.warn{color:var(--warn)} .status.bad{color:var(--bad)}

/* ---- path ---- */
.path{display:flex;flex-wrap:wrap;gap:6px;max-height:150px;overflow:auto;padding:2px}
.step{border:1px solid var(--line);background:#ffffff08;border-radius:9px;padding:4px 9px;font-size:12px;cursor:pointer;
  color:var(--muted);font-variant-numeric:tabular-nums}
.step:hover{color:var(--text)}
.step.now{background:linear-gradient(135deg,var(--tile1),var(--tile2));color:#fff;border-color:transparent}
.step.done{color:var(--text)}

/* ---- compare ---- */
table{width:100%;border-collapse:collapse;font-size:13px}
th{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);text-align:right;padding:6px 8px;font-weight:600}
th:first-child,td:first-child{text-align:left}
td{padding:9px 8px;border-top:1px solid var(--line);text-align:right;font-variant-numeric:tabular-nums}
td.name{font-weight:600}
td .bar{height:5px;border-radius:5px;margin-top:6px;background:linear-gradient(90deg,var(--tile1),var(--accent2));min-width:2px}
tr.sel td.name{color:var(--accent2)}
.tablewrap{overflow-x:auto}
tr.click{cursor:pointer} tr.click:hover td{background:#ffffff08}
.empty{color:var(--muted);font-size:13px;padding:6px 0}

/* ---- overlay ---- */
.overlay{position:fixed;inset:0;background:#050810b0;display:none;place-items:center;z-index:10;backdrop-filter:blur(3px)}
.overlay.show{display:grid}
.spin{width:44px;height:44px;border-radius:50%;border:4px solid #ffffff22;border-top-color:var(--accent2);animation:rot .8s linear infinite;margin:0 auto 14px}
@keyframes rot{to{transform:rotate(360deg)}}
.box{text-align:center;background:#12183aee;border:1px solid var(--line);padding:26px 34px;border-radius:18px}
.box small{color:var(--muted)}
.kbd{font-size:11px;color:var(--muted);text-align:center;margin-top:14px}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">8</div>
    <div>
      <h1>8-Puzzle Solver</h1>
      <p>BFS · DFS · Iterative Deepening · A* (Manhattan &amp; Euclidean)</p>
    </div>
  </header>

  <div class="grid">
    <!-- LEFT: board -->
    <div class="card">
      <h2>Board</h2>
      <div class="board" id="board"></div>
      <div class="scrub">
        <input type="range" id="scrub" min="0" max="0" value="0" disabled>
      </div>
      <div class="stepinfo"><span>Step <b id="stepNo">0</b> / <b id="stepTot">0</b></span><span id="moveLbl">—</span></div>
      <div class="transport">
        <button class="btn icon" id="first" title="First step" disabled>⏮</button>
        <button class="btn icon" id="prev"  title="Previous (←)" disabled>◀</button>
        <button class="btn primary play" id="play" title="Play / pause (space)" disabled>▶</button>
        <button class="btn icon" id="next"  title="Next (→)" disabled>▶</button>
        <button class="btn icon" id="last"  title="Last step" disabled>⏭</button>
      </div>
      <div class="speed">Speed <input type="range" id="speed" min="1" max="10" value="6"><span id="speedLbl">6</span></div>
      <div class="kbd">Tip: click a tile next to the blank to move it yourself · Space = play/pause · ← → = step</div>
    </div>

    <!-- RIGHT -->
    <div class="stack">
      <div class="card">
        <h2>Initial state</h2>
        <div class="row">
          <input type="text" id="stateIn" value="1,2,5,3,4,0,6,7,8" spellcheck="false" aria-label="Initial state">
          <button class="btn" id="apply">Set</button>
          <button class="btn" id="shuffle">🎲 Shuffle</button>
          <button class="btn" id="sample">Lab sample</button>
        </div>
        <div class="hint" id="hint">Nine numbers 0–8 (0 = blank), row by row. Goal: 0,1,2,3,4,5,6,7,8</div>
      </div>

      <div class="card">
        <h2>Algorithm</h2>
        <div class="chips" id="chips"></div>
        <div class="row" style="margin-top:14px">
          <button class="btn primary" id="solve">Solve</button>
          <button class="btn" id="compare">Compare all</button>
          <span style="flex:1"></span>
          <label style="font-size:12px;color:var(--muted)">Time limit
            <select id="timeout"><option value="10">10 s</option><option value="30" selected>30 s</option>
            <option value="60">60 s</option><option value="120">2 min</option></select></label>
        </div>
        <div class="status" id="status">Pick an algorithm and press Solve.</div>
      </div>

      <div class="card">
        <h2>Result</h2>
        <div class="stats">
          <div class="stat"><span>Cost</span><b id="sCost">—</b></div>
          <div class="stat"><span>Expanded</span><b id="sExp">—</b></div>
          <div class="stat"><span>Depth</span><b id="sDepth">—</b></div>
          <div class="stat"><span>Max depth</span><b id="sMax">—</b></div>
          <div class="stat"><span>Time</span><b id="sTime">—</b></div>
        </div>
        <h2 style="margin-top:18px">Path to goal <small style="text-transform:none;letter-spacing:0">(direction the blank moves)</small></h2>
        <div class="path" id="path"><span class="empty">No solution yet.</span></div>
      </div>

      <div class="card">
        <h2>Comparison for this state</h2>
        <div class="tablewrap" id="cmp"><div class="empty">Run “Compare all” to fill this table.</div></div>
      </div>
    </div>
  </div>
</div>

<div class="overlay" id="busy"><div class="box"><div class="spin"></div><div id="busyMsg">Solving…</div><small>Slow algorithms are stopped at the time limit.</small></div></div>

<script>
const GOAL=[0,1,2,3,4,5,6,7,8];
const ALGOS=[["bfs","BFS"],["dfs","DFS"],["ids","Iterative DFS"],["astar-manhattan","A* Manhattan"],["astar-euclidean","A* Euclidean"]];
const LABEL=Object.fromEntries(ALGOS);
const ARROW={Up:"↑",Down:"↓",Left:"←",Right:"→"};
const $=id=>document.getElementById(id);

let algo="astar-manhattan";
let cur=[1,2,5,3,4,0,6,7,8];     // board currently displayed
let start=cur.slice();           // initial state of the problem
let sol=null;                    // {states,path} being replayed
let idx=0, timer=null, results={}, lastMoved=null;

/* ---------- board ---------- */
const board=$("board"), tiles={};
for(let i=0;i<9;i++){const s=document.createElement("div");s.className="slot";
  s.style.setProperty("--r",Math.floor(i/3));s.style.setProperty("--c",i%3);board.appendChild(s);}
for(let t=1;t<=8;t++){const d=document.createElement("div");d.className="tile";d.textContent=t;
  d.onclick=()=>manual(t);board.appendChild(d);tiles[t]=d;}

function draw(){
  cur.forEach((t,i)=>{ if(t===0)return; const el=tiles[t];
    el.style.setProperty("--r",Math.floor(i/3));el.style.setProperty("--c",i%3);
    el.classList.toggle("ok",GOAL[i]===t); el.classList.toggle("moved",t===lastMoved);});
  const done=cur.every((t,i)=>t===GOAL[i]);
  if(done&&sol&&idx>0){board.classList.remove("solved");void board.offsetWidth;board.classList.add("solved");}
}
function manual(t){           // user clicks a tile
  stop(); const b=cur.indexOf(0), i=cur.indexOf(t);
  const [br,bc]=[Math.floor(b/3),b%3],[r,c]=[Math.floor(i/3),i%3];
  if(Math.abs(br-r)+Math.abs(bc-c)!==1)return;
  cur[b]=t;cur[i]=0;lastMoved=t;start=cur.slice();clearSolution(true);draw();
  $("stateIn").value=cur.join(",");results={};renderCmp();
}

/* ---------- state input ---------- */
function parse(txt){
  let a=txt.replace(/[\s\[\]\(\)]/g,"");
  a=a.includes(",")?a.split(",").filter(x=>x!==""):a.split("");
  const n=a.map(Number);
  if(n.length!==9||n.some(x=>!Number.isInteger(x))||[...n].sort().join()!==GOAL.join())
    throw new Error("Enter each of 0–8 exactly once, e.g. 1,2,5,3,4,0,6,7,8");
  return n;
}
function solvable(s){const t=s.filter(x=>x);let inv=0;
  for(let i=0;i<t.length;i++)for(let j=i+1;j<t.length;j++)if(t[i]>t[j])inv++;return inv%2===0;}
function setHint(msg,err){$("hint").textContent=msg;$("hint").className="hint"+(err?" err":"");$("stateIn").classList.toggle("bad",!!err);}
function setState(s){stop();start=s.slice();cur=s.slice();lastMoved=null;clearSolution();results={};renderCmp();
  $("stateIn").value=s.join(",");draw();
  solvable(s)?setHint("Nine numbers 0–8 (0 = blank), row by row. Goal: 0,1,2,3,4,5,6,7,8")
             :setHint("This board is not solvable (odd number of inversions).",true);}
$("apply").onclick=()=>{try{setState(parse($("stateIn").value));}catch(e){setHint(e.message,true);}};
$("stateIn").addEventListener("keydown",e=>{if(e.key==="Enter")$("apply").click();});
$("shuffle").onclick=async()=>{const r=await fetch("/api/random");setState((await r.json()).state);};
$("sample").onclick=()=>setState([1,2,5,3,4,0,6,7,8]);

/* ---------- algorithm chips ---------- */
ALGOS.forEach(([k,l])=>{const c=document.createElement("button");c.className="chip"+(k===algo?" on":"");
  c.textContent=l;c.dataset.k=k;c.onclick=()=>{algo=k;document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("on",x.dataset.k===k));
    if(results[k])show(k);};$("chips").appendChild(c);});

/* ---------- solving ---------- */
async function run(algos){
  if(!solvable(start)){setHint("This board is not solvable (odd number of inversions).",true);return;}
  stop();$("busy").classList.add("show");
  $("busyMsg").textContent=algos.length>1?"Running all algorithms…":"Solving with "+LABEL[algos[0]]+"…";
  try{
    const r=await fetch("/api/solve",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({state:start,algos,timeout:+$("timeout").value})});
    const j=await r.json(); if(!r.ok)throw new Error(j.error);
    Object.assign(results,j.results); renderCmp(); show(algos.includes(algo)?algo:algos[0]);
    if(!algos.includes(algo)){algo=algos[0];document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("on",x.dataset.k===algo));}
  }catch(e){status(e.message,"bad");}
  finally{$("busy").classList.remove("show");}
}
$("solve").onclick=()=>run([algo]);
$("compare").onclick=()=>run(ALGOS.map(a=>a[0]));

function status(msg,cls){$("status").textContent=msg;$("status").className="status "+(cls||"");}
const fmt=n=>n==null?"—":n.toLocaleString("en-US");
const fmtT=t=>t==null?"—":(t<0.001?"<1 ms":t<1?(t*1000).toFixed(1)+" ms":t.toFixed(2)+" s");

function show(k){
  const r=results[k]; if(!r)return; clearSolution(true);
  if(r.timed_out){["sCost","sExp","sDepth","sMax"].forEach(i=>$(i).textContent="—");$("sTime").textContent=">"+r.time+" s";
    status(LABEL[k]+" hit the time limit — raise it or try A*.","warn");renderCmp();return;}
  $("sCost").textContent=fmt(r.cost);$("sExp").textContent=fmt(r.nodes_expanded);
  $("sDepth").textContent=fmt(r.search_depth);$("sMax").textContent=fmt(r.max_depth);$("sTime").textContent=fmtT(r.time);
  renderCmp();
  if(!r.solved){status("No solution found.","bad");return;}
  if(!r.states){status(`${LABEL[k]} found a ${fmt(r.cost)}-move path — too long to animate, see the numbers above.`,"warn");
    $("path").innerHTML='<span class="empty">Path has '+fmt(r.cost)+' moves (too long to list).</span>';return;}
  sol={states:r.states,path:r.path};idx=0;cur=sol.states[0].slice();lastMoved=null;
  status(`${LABEL[k]}: solved in ${r.cost} moves. Press ▶ to watch it.`,"good");
  buildPath();syncUI();draw();
}
function clearSolution(keepStats){
  sol=null;idx=0;$("path").innerHTML='<span class="empty">No solution yet.</span>';
  if(!keepStats){["sCost","sExp","sDepth","sMax","sTime"].forEach(i=>$(i).textContent="—");}
  syncUI();
}

/* ---------- playback ---------- */
function buildPath(){
  const p=$("path");p.innerHTML="";
  if(!sol.path.length){p.innerHTML='<span class="empty">Already at the goal.</span>';return;}
  sol.path.forEach((m,i)=>{const s=document.createElement("span");s.className="step";s.dataset.i=i+1;
    s.textContent=(i+1)+" "+ARROW[m];s.title="Step "+(i+1)+": blank moves "+m;s.onclick=()=>{stop();go(i+1);};p.appendChild(s);});
}
function go(i){
  if(!sol)return; idx=Math.max(0,Math.min(sol.states.length-1,i));
  const prev=cur, nxt=sol.states[idx].slice(); cur=nxt;
  const b=prev.indexOf(0);lastMoved=idx>0?prev[nxt.indexOf(0)]:null;   // tile that slid into the old blank
  draw();syncUI();
}
function syncUI(){
  const n=sol?sol.states.length-1:0;
  $("scrub").max=n;$("scrub").value=idx;$("scrub").disabled=!sol;
  $("stepNo").textContent=idx;$("stepTot").textContent=n;
  $("moveLbl").textContent=sol&&idx>0?"blank moves "+sol.path[idx-1]+" "+ARROW[sol.path[idx-1]]:"—";
  ["first","prev","next","last","play"].forEach(id=>$(id).disabled=!sol);
  $("play").textContent=timer?"⏸":"▶";
  document.querySelectorAll(".step").forEach(s=>{const i=+s.dataset.i;s.classList.toggle("now",i===idx);s.classList.toggle("done",i<idx);});
  const now=document.querySelector(".step.now");if(now)now.scrollIntoView({block:"nearest",inline:"nearest"});
}
function stop(){if(timer){clearInterval(timer);timer=null;}syncUI();}
function play(){
  if(!sol)return; if(timer){stop();return;}
  if(idx>=sol.states.length-1)go(0);
  const ms=1100-+$("speed").value*100;
  timer=setInterval(()=>{ if(idx>=sol.states.length-1){stop();return;} go(idx+1); },ms);syncUI();
}
$("play").onclick=play;$("next").onclick=()=>{stop();go(idx+1);};$("prev").onclick=()=>{stop();go(idx-1);};
$("first").onclick=()=>{stop();go(0);};$("last").onclick=()=>{stop();go(sol.states.length-1);};
$("scrub").oninput=e=>{stop();go(+e.target.value);};
$("speed").oninput=e=>{$("speedLbl").textContent=e.target.value;if(timer){stop();play();}};
document.addEventListener("keydown",e=>{ if(e.target.tagName==="INPUT"&&e.target.type==="text")return;
  if(e.code==="Space"){e.preventDefault();play();} else if(e.key==="ArrowRight"){stop();go(idx+1);} else if(e.key==="ArrowLeft"){stop();go(idx-1);}});

/* ---------- comparison table ---------- */
function renderCmp(){
  const keys=ALGOS.map(a=>a[0]).filter(k=>results[k]);
  if(!keys.length){$("cmp").innerHTML='<div class="empty">Run “Compare all” to fill this table.</div>';return;}
  const done=keys.filter(k=>results[k].solved);
  const mx=Math.max(1,...done.map(k=>Math.log10(results[k].nodes_expanded+1)));
  let h="<table><tr><th>Algorithm</th><th>Cost</th><th>Expanded</th><th>Depth</th><th>Time</th></tr>";
  keys.forEach(k=>{const r=results[k];
    if(r.timed_out){h+=`<tr class="click ${k===algo?"sel":""}" data-k="${k}"><td class="name">${LABEL[k]}</td><td colspan="4" style="color:var(--warn)">time limit (&gt; ${r.time} s)</td></tr>`;return;}
    const w=r.solved?Math.max(2,100*Math.log10(r.nodes_expanded+1)/mx):0;
    h+=`<tr class="click ${k===algo?"sel":""}" data-k="${k}"><td class="name">${LABEL[k]}</td><td>${fmt(r.cost)}</td>
      <td>${fmt(r.nodes_expanded)}<div class="bar" style="width:${w}%"></div></td><td>${fmt(r.search_depth)}</td><td>${fmtT(r.time)}</td></tr>`;});
  $("cmp").innerHTML=h+"</table><div class='hint'>Bars use a log scale. Click a row to replay that solution.</div>";
  document.querySelectorAll("#cmp tr.click").forEach(tr=>tr.onclick=()=>{algo=tr.dataset.k;
    document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("on",x.dataset.k===algo));show(algo);});
}

draw();syncUI();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    serve(port)
