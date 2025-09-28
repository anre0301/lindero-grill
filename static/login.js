// ===== Config =====
const PIN_LENGTH = 4;

// ===== DOM =====
const dots    = document.querySelectorAll("#dots span");
const pad     = document.querySelector(".pad");
const ok      = document.getElementById("ok");
const msg     = document.getElementById("msg");
const overlay = document.getElementById("loading");
const card    = document.getElementById("loginCard");

let buffer = "";
let submitting = false;

// Actualiza los puntos del PIN
function updateDots(){
  dots.forEach((d,i)=> d.classList.toggle("fill", i < buffer.length));
}

// Agregar / borrar dígitos
function push(k){
  if(submitting) return;
  if(k === "x"){
    buffer = buffer.slice(0,-1);
    updateDots();
    return;
  }
  if(/^\d$/.test(k) && buffer.length < PIN_LENGTH){
    buffer += k;
    updateDots();
  }
}

// Mostrar/ocultar loading
function showLoading(show=true){
  overlay.classList.toggle("show", show);
  overlay.style.display = show ? "grid" : "none";
  if(ok) ok.disabled = show;
  if(card) card.style.filter = show ? "blur(1px) brightness(.94)" : "none";
}

// Enviar PIN (mínimo 2s de loader)
async function submit(){
  if(submitting) return;
  if(buffer.length !== PIN_LENGTH){
    msg.textContent = `Completa los ${PIN_LENGTH} dígitos.`;
    return;
  }
  submitting = true;
  msg.textContent = "";
  showLoading(true);
  const start = Date.now();

  try{
    const r = await fetch("/verify-pin", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ pin: buffer })
    });
    let data = {};
    try { data = await r.json(); } catch {}

    if(r.ok && data.ok){
      const elapsed = Date.now() - start;
      const delay = Math.max(0, 2000 - elapsed); // al menos 2s
      setTimeout(()=> location.href = "/panel", delay);
      return;
    }
    buffer = ""; updateDots();
    msg.textContent = (data && data.error) ? data.error : "PIN incorrecto";
    if(navigator.vibrate) navigator.vibrate(120);
  }catch(e){
    console.error(e);
    msg.textContent = "Error de conexión";
  }finally{
    submitting = false;
    setTimeout(()=> showLoading(false), 2000);
  }
}

// Eventos
pad.addEventListener("click", (e)=>{
  const btn = e.target.closest("button");
  if(!btn) return;
  if(btn.id === "ok"){ submit(); return; }
  const k = btn.dataset.k; if(!k) return;
  push(k);
});
ok.addEventListener("click", submit);

document.addEventListener("keydown", (e)=>{
  if(e.key >= "0" && e.key <= "9") push(e.key);
  else if(e.key === "Backspace") push("x");
  else if(e.key === "Enter") submit();
});
