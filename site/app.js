(function(){
'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const norm=s=>(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const nf=new Intl.NumberFormat('es-ES');
const cap=s=>s.charAt(0).toUpperCase()+s.slice(1);
const pad=n=>String(n).padStart(2,'0');

// ---------- almacenamiento (solo con consentimiento) ----------
const PFX='campana.', PREFS=['theme','fav','rad','filt','ord'];
const store=k=>(k==='theme'||k==='fav')?localStorage:sessionStorage;
function CONSENT(){try{const c=JSON.parse(localStorage.getItem(PFX+'consent'));if(c&&Date.now()-c.t<365*864e5)return c}catch(e){}return null}
function setConsent(pref){try{localStorage.setItem(PFX+'consent',JSON.stringify({pref:!!pref,t:Date.now(),v:1}))}catch(e){}
  if(!pref)PREFS.forEach(k=>{try{localStorage.removeItem(PFX+k);sessionStorage.removeItem(PFX+k)}catch(e){}})}
const canSave=()=>{const c=CONSENT();return !!(c&&c.pref)};
const LS={get(k){try{return JSON.parse(store(k).getItem(PFX+k))}catch(e){return null}},set(k,v){if(!canSave())return;try{store(k).setItem(PFX+k,JSON.stringify(v))}catch(e){}}};

// ---------- datos (un archivo por diócesis, se cargan según dónde estés) ----------
const IDX=window.CAMPANA_IDX, META={built:IDX.built,fallos:IDX.dioc.filter(d=>d.estado!=='ok')};
const C=[], PLACES=[], LOADED=new Set(); let LOADING=0;
const DEFLOC={lat:36.2825,lon:-5.2945,label:'Sotogrande',def:true};
const BASEPL=[['Sotogrande',36.2825,-5.2945],['Gibraltar',36.1408,-5.3536],['Algeciras',36.1408,-5.4562],['La Línea de la Concepción',36.1681,-5.3478],['San Roque',36.2103,-5.3844],['Estepona',36.4276,-5.1459],['Manilva',36.3777,-5.2506],['Casares',36.4459,-5.2736],['Marbella',36.5100,-4.8825],['Tarifa',36.0143,-5.6044],['Los Barrios',36.1856,-5.4912],['Jimena de la Frontera',36.4343,-5.4531],['Castellar de la Frontera',36.2886,-5.4533],['Gaucín',36.5170,-5.3189],
 ['Sevilla',37.3891,-5.9845],['Málaga',36.7213,-4.4214],['Cádiz',36.5271,-6.2886],['Jerez de la Frontera',36.6850,-6.1261],['Córdoba',37.8882,-4.7794],['Granada',37.1773,-3.5986],['Almería',36.8340,-2.4637],['Huelva',37.2614,-6.9447],['Jaén',37.7796,-3.7849],['Madrid',40.4168,-3.7038],['Barcelona',41.3874,2.1686],['Valencia',39.4699,-0.3763],['Zaragoza',41.6488,-0.8891],['Bilbao',43.2630,-2.9350],['Alicante',38.3452,-0.4810],['Murcia',37.9922,-1.1307],['Palma de Mallorca',39.5696,2.6502],['Las Palmas de Gran Canaria',28.1235,-15.4363],['Santa Cruz de Tenerife',28.4636,-16.2518],['Valladolid',41.6523,-4.7245],['Vigo',42.2406,-8.7207],['A Coruña',43.3623,-8.4115],['Santander',43.4623,-3.8100],['Pamplona',42.8125,-1.6458],['San Sebastián',43.3183,-1.9812],['Oviedo',43.3614,-5.8593],['Toledo',39.8628,-4.0273],['Salamanca',40.9701,-5.6635],['Burgos',42.3439,-3.6969],['Logroño',42.4627,-2.4450],['Badajoz',38.8794,-6.9707],['Santiago de Compostela',42.8782,-8.5448]];
function enrich(c){
  const addr=[c.calle&&(c.calle+(c.num?', '+c.num:'')),c.cp,c.localidad].filter(Boolean).join(', ');
  return {...c,i:C.length,addr,en:(c.idiomas||[]).includes('en'),k:norm(c.nombre+' '+c.localidad)};
}
function rebuildPlaces(){
  const PL={};
  C.forEach(c=>{const k=norm(c.localidad);const p=PL[k]||(PL[k]={n:c.localidad,lat:0,lon:0,c:0});p.lat+=c.lat;p.lon+=c.lon;p.c++});
  PLACES.length=0;
  Object.values(PL).forEach(p=>PLACES.push({n:p.n,lat:p.lat/p.c,lon:p.lon/p.c,c:p.c,k:norm(p.n)}));
  BASEPL.forEach(([n,lat,lon])=>{const k=norm(n);if(!PLACES.some(p=>p.k===k||p.k.startsWith(k)||k.startsWith(p.k)))PLACES.push({n,lat,lon,c:0,k})});
}
function bboxKm(lat,lon,b){return distKm(lat,lon,Math.min(Math.max(lat,b[0]),b[2]),Math.min(Math.max(lon,b[1]),b[3]))}
function loadDioc(id){
  return new Promise(res=>{
    if(LOADED.has(id))return res(false);
    LOADED.add(id); LOADING++;
    const s=document.createElement('script'); s.src='data/'+id+'.js?v='+IDX.built.replace(/\D/g,'');
    const fin=ok=>{LOADING--;if(ok){(window.CAMPANA_DATA[id]||[]).forEach(c=>C.push(enrich(c)));rebuildPlaces()}else LOADED.delete(id);res(ok)};
    s.onload=()=>fin(true); s.onerror=()=>fin(false); document.head.appendChild(s);
  });
}
// carga las diócesis cuyo territorio está a menos de r km del punto; devuelve true si ha cargado algo
function ensureNear(lat,lon,r){
  const need=IDX.dioc.filter(d=>!LOADED.has(d.id)&&bboxKm(lat,lon,d.bbox)<=(r||60));
  return Promise.all(need.map(d=>loadDioc(d.id))).then(a=>a.some(Boolean));
}
rebuildPlaces();

// ---------- hora de Madrid ----------
const fm=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
function nowMad(){const o={};fm.formatToParts(new Date()).forEach(p=>o[p.type]=p.value);return {date:`${o.year}-${o.month}-${o.day}`,min:(+o.hour)*60+(+o.minute)}}
let NOW=nowMad();
const addDays=(ds,k)=>{const d=new Date(ds+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+k);return d.toISOString().slice(0,10)};
const dowOf=ds=>(new Date(ds+'T12:00:00Z').getUTCDay()+6)%7; // 0 = lunes
const DOWS=['lunes','martes','miércoles','jueves','viernes','sábado','domingo'];
const DOW3=['lun','mar','mié','jue','vie','sáb','dom'];
const MES=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const dnum=ds=>+ds.slice(8,10), mnum=ds=>+ds.slice(5,7);
const dur=m=>m<60?m+' min':Math.floor(m/60)+' h'+(m%60?' '+(m%60)+' min':'');
const tmin=t=>+t.slice(0,2)*60+ +t.slice(3,5);

// ---------- horarios: temporada, tipo de día y próximas misas ----------
function lastSun(y,m){const d=new Date(Date.UTC(y,m,0,12));while(d.getUTCDay()!==0)d.setUTCDate(d.getUTCDate()-1);return d.getUTCDate()}
function isSummer(c,ds){
  const y=+ds.slice(0,4),m=mnum(ds),d=dnum(ds),v=m*100+d,r=c.verano;
  if(r==='dst'){return v>=300+lastSun(y,3)&&v<1000+lastSun(y,10)}
  if(Array.isArray(r)){const s=r[0]*100+r[1],e=r[2]*100+r[3];return s<=e?(v>=s&&v<=e):(v>=s||v<=e)}
  return m>=6&&m<=9;
}
const HOL=new Set(['01-01','01-06','05-01','08-15','10-12','11-01','12-06','12-08','12-25']);
function kindOf(ds){const w=dowOf(ds);if(w===6||HOL.has(ds.slice(5)))return 'fest';if(w===5)return 'visp';return 'lab'}
const emptySeason=s=>!s||!(s.lab.some(l=>l.length)||s.visp.length||s.fest.length);
function seasonOf(c,ds){
  const k=isSummer(c,ds)?'ver':'inv', o=k==='ver'?'inv':'ver';
  if(emptySeason(c.h[k])&&!emptySeason(c.h[o]))return {s:o,fb:true,h:c.h[o]};
  return {s:k,fb:false,h:c.h[k]};
}
function timesOn(c,ds){
  const {h,fb,s}=seasonOf(c,ds), k=kindOf(ds);
  const t=k==='lab'?(h.lab[dowOf(ds)]||[]):(h[k]||[]);
  return {t:[...new Set(t)].sort(),fb,s,k};
}
const DUR=50; // una misa se considera "en curso" hasta 50 min después de empezar
function upcoming(c,now,maxDays,limit){
  const out=[];
  for(let k=0;k<=maxDays&&out.length<limit;k++){
    const ds=addDays(now.date,k), {t,fb}=timesOn(c,ds);
    for(const x of t){const abs=k*1440+tmin(x);if(abs>=now.min-DUR)out.push({ds,t:x,abs,k,fb})}
  }
  return out;
}
const whenLabel=(m,short)=>m.k===0?(short?'':'hoy '):m.k===1?'mañana ':DOW3[dowOf(m.ds)]+' '+dnum(m.ds)+' ';
function status(c){
  const u=upcoming(c,NOW,8,5); c._u=u;
  if(!u.length)return {k:'nd',t:'Sin horario',d:c.interpretado?'sin misas en 8 días':'no disponible'};
  const f=u[0], dl=f.abs-NOW.min;
  if(dl<=0)return {k:'curso',t:'En curso',d:'empezó a las '+f.t};
  if(dl<=60)return {k:'pronto',t:'En '+dur(dl),d:'a las '+f.t};
  if(f.k===0)return {k:'hoy',t:'Hoy '+f.t,d:'en '+dur(dl)};
  if(f.k===1)return {k:'luego',t:'Mañana '+f.t,d:''};
  return {k:'luego',t:cap(DOW3[dowOf(f.ds)])+' '+f.t,d:dnum(f.ds)+' '+MES[mnum(f.ds)-1]};
}

// ---------- geografía ----------
function distKm(a,b,c,d){const R=6371,r=Math.PI/180,dp=(c-a)*r,dl=(d-b)*r;const h=Math.sin(dp/2)**2+Math.cos(a*r)*Math.cos(c*r)*Math.sin(dl/2)**2;return 2*R*Math.asin(Math.sqrt(h))}
const fmtKm=k=>k<0.95?Math.round(k*100)*10+' m':(k<9.95?k.toFixed(1).replace('.',','):Math.round(k))+' km';
const eta=k=>Math.max(3,Math.round(k*1.35/(k<4?30:50)*60)); // minutos en coche, estimación por distancia en línea recta
const route=c=>`https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lon}`;
const telFmt=t=>(t||'').replace(/\D/g,'').replace(/^34/,'').replace(/(\d{3})(\d{3})(\d{3})/,'$1 $2 $3');

// ---------- estado ----------
let LOC=Object.assign({},DEFLOC), RAD=+(LS.get('rad')||25), FILT=LS.get('filt')||'todas', ORD=LS.get('ord')||'cerca';
let SEL=null, VIEW='cerca', WDAY=null, WFILT='todas', SEAS=null, GPSOK=false;
let FAV=new Set(LS.get('fav')||[]);
const isFav=c=>FAV.has(c.id);
$('#rad').value=String(RAD);
const ROWS=[]; // iglesias visibles, ordenadas

// ---------- iconos ----------
const ICON={
  bell:'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6a1.4 1.4 0 0 1 1.4 1.4v.45A6.2 6.2 0 0 1 18.2 10.5v3.2l1.75 2.5a1 1 0 0 1-.82 1.58H4.87a1 1 0 0 1-.82-1.58l1.75-2.5v-3.2a6.2 6.2 0 0 1 4.8-6.05V4A1.4 1.4 0 0 1 12 2.6z"/><path d="M9.4 19h5.2a2.6 2.6 0 0 1-5.2 0z"/></svg>',
  go:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11.5 21 3l-8.5 18-2-7.5z"/></svg>',
  tel:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2"/></svg>',
  ext:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
  star:'<svg viewBox="0 0 24 24"><path d="M12 3.4l2.6 5.4 5.9.8-4.3 4.1 1 5.9L12 16.8 6.8 19.6l1-5.9L3.5 9.6l5.9-.8z"/></svg>'
};
const starBtn=c=>`<button type="button" class="stbtn" data-fav="${c.i}" aria-pressed="${isFav(c)}" aria-label="${isFav(c)?'Quitar de favoritas':'Añadir a favoritas'}: ${esc(c.nombre)}" title="${isFav(c)?'Quitar de favoritas':'Añadir a favoritas'}">${ICON.star}</button>`;
const langBadge=c=>(c.en?'<span class="badge">EN</span>':'')+(c.res?'<span class="badge warn">Residencia</span>':'');

// ---------- toast ----------
let toastT=0;
function toast(html,ms){const t=$('#toast');t.innerHTML=html;t.hidden=false;clearTimeout(toastT);toastT=setTimeout(()=>{t.hidden=true},ms||5000)}

// ---------- favoritas ----------
function toggleFav(i){
  const c=C[i]; if(!c)return;
  if(FAV.has(c.id))FAV.delete(c.id);else FAV.add(c.id);
  if(canSave())LS.set('fav',[...FAV]);
  else if(FAV.has(c.id))toast('Favorita añadida. Se perderá al cerrar la web. <button type="button" class="btn ck" id="tSave" style="height:30px;margin-left:8px">Guardar en este dispositivo</button>',9000);
  render();
}
document.addEventListener('click',e=>{if(e.target.id==='tSave'){setConsent(true);LS.set('fav',[...FAV]);LS.set('rad',RAD);LS.set('filt',FILT);LS.set('ord',ORD);toast('Guardado en este dispositivo.',3000)}});

// ---------- buscador ----------
const q=$('#q'), sug=$('#sug'); let hits=[],hl=-1;
function search(s){
  const k=norm(s); if(!k)return [];
  const out=[];
  PLACES.forEach(p=>{if(p.k.startsWith(k)||p.k.includes(' '+k))out.push({t:'p',n:p.n,sub:p.c?p.c+(p.c>1?' iglesias':' iglesia'):'Lugar',lat:p.lat,lon:p.lon,r:p.k===k?0:p.k.startsWith(k)?1:2})});
  C.forEach(c=>{if(c.k.includes(k))out.push({t:'c',n:c.nombre,sub:c.localidad,i:c.i,r:3})});
  out.sort((a,b)=>a.r-b.r);
  return out.slice(0,8);
}
function showSug(){
  hits=search(q.value); hl=-1;
  if(!q.value.trim()){sug.hidden=true;return}
  sug.innerHTML=hits.length?hits.map((h,i)=>`<button type="button" data-i="${i}">${esc(h.n)}<span>${esc(h.t==='c'?'Iglesia · '+h.sub:h.sub)}</span></button>`).join(''):'<div class="none">No encuentro ese lugar. Prueba con el municipio o el nombre de la iglesia.</div>';
  sug.hidden=false;
}
q.addEventListener('input',showSug);
q.addEventListener('focus',()=>{if(q.value.trim())showSug()});
q.addEventListener('keydown',e=>{
  if(sug.hidden)return;
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();hl=(hl+(e.key==='ArrowDown'?1:-1)+hits.length)%hits.length;[...sug.querySelectorAll('button')].forEach((b,i)=>b.classList.toggle('hl',i===hl))}
  if(e.key==='Escape')sug.hidden=true;
});
sug.addEventListener('mousedown',e=>{const b=e.target.closest('button');if(b){e.preventDefault();pick(hits[+b.dataset.i])}});
document.addEventListener('click',e=>{if(!e.target.closest('#tool'))sug.hidden=true});
$('#tool').addEventListener('submit',e=>{e.preventDefault();if(!hits.length)hits=search(q.value);if(hits.length)pick(hits[Math.max(0,hl)])});
function pick(h){
  if(!h)return; sug.hidden=true;
  if(h.t==='c'){q.value='';select(h.i,true);return}
  setLoc({lat:h.lat,lon:h.lon,label:h.n});
}
$('#rad').addEventListener('change',e=>{RAD=+e.target.value;LS.set('rad',RAD);MAP.center(LOC.lat,LOC.lon,RAD);render()});

// ---------- ubicación ----------
function nearestPlace(lat,lon){let b=null,bd=1e9;PLACES.forEach(p=>{const d=distKm(lat,lon,p.lat,p.lon);if(d<bd){bd=d;b=p}});return {p:b,d:bd}}
function setLoc(l){LOC=l; SEL=null; q.value=l.def?'':l.label; MAP.center(l.lat,l.lon,RAD); render(); if(VIEW!=='cerca'&&VIEW!=='semana')location.hash='cerca';
  ensureNear(l.lat,l.lon,Math.max(RAD,25)+25).then(ch=>{if(ch&&LOC===l){SEL=null;render()}})}
function gps(auto){
  const m=$('#gmsg');
  const fail=why=>{
    if(auto){m.hidden=false;m.textContent='No he podido leer tu ubicación'+(why?' ('+why+')':'')+'. Muestro Sotogrande; pulsa «Mi ubicación» o escribe un lugar.';}
    else{m.hidden=false;m.textContent='No he podido leer tu ubicación (permiso denegado o no disponible). Escribe tu municipio, barrio o iglesia.'}
  };
  if(!navigator.geolocation)return fail('no disponible en este navegador');
  if(!auto){m.hidden=false;m.textContent='Pidiendo tu ubicación…'}
  try{
    navigator.geolocation.getCurrentPosition(p=>{
      m.hidden=true; GPSOK=true;
      const {p:pl,d}=nearestPlace(p.coords.latitude,p.coords.longitude);
      setLoc({lat:p.coords.latitude,lon:p.coords.longitude,label:d<12&&pl?'Tu ubicación · cerca de '+pl.n:'Tu ubicación',gps:true});
    },err=>fail(err&&err.code===1?'permiso denegado':''),{timeout:9000,maximumAge:60000,enableHighAccuracy:false});
  }catch(e){fail('')}
}
$('#gps').addEventListener('click',()=>gps(false));
function renderQuick(){
  const names=['Sotogrande','Guadiaro','Torreguadiaro','San Roque','La Línea de la Concepción','Estepona','Algeciras','Manilva'];
  const arr=names.map(n=>PLACES.find(p=>p.k===norm(n))).filter(Boolean).slice(0,7);
  $('#quick').innerHTML=(GPSOK?'':'')+arr.map((p,i)=>{
    const on=!LOC.gps&&Math.abs(LOC.lat-p.lat)<2e-3&&Math.abs(LOC.lon-p.lon)<2e-3;
    return `<button type="button" class="qchip" data-p="${esc(p.k)}" aria-pressed="${on}">${p.c?'<i class="dot"></i>':''}${esc(p.n.replace('de la Concepción',''))}</button>`}).join('');
}
$('#quick').addEventListener('click',e=>{const b=e.target.closest('.qchip');if(!b)return;const p=PLACES.find(x=>x.k===b.dataset.p);if(p)setLoc({lat:p.lat,lon:p.lon,label:p.n.replace(' de la Concepción','')})});

// ---------- cálculo ----------
function compute(){
  NOW=nowMad();
  ROWS.length=0;
  for(const c of C){
    const d=distKm(LOC.lat,LOC.lon,c.lat,c.lon); c._d=d; c._s=status(c);
    if(d<=RAD)ROWS.push(c);
  }
}
function passes(c){
  if(FILT==='hoy')return c._u&&c._u[0]&&c._u[0].k===0;
  if(FILT==='en')return c.en;
  if(FILT==='fav')return isFav(c);
  return true;
}
function sorted(){
  const a=ROWS.filter(passes);
  if(ORD==='antes')a.sort((x,y)=>((x._u[0]?x._u[0].abs:1e9)-(y._u[0]?y._u[0].abs:1e9))||x._d-y._d);
  else a.sort((x,y)=>x._d-y._d);
  return a;
}
// las dos tarjetas de arriba: la más cercana y la primera que puedes alcanzar
function heroes(){
  const arr=C.filter(c=>!c.res).map(c=>{const e=eta(c._d);const m=(c._u||[]).find(x=>x.abs-NOW.min>=e-5);return {c,d:c._d,e,m}}).filter(x=>x.m);
  if(!arr.length)return null;
  // la más cercana: entre las que tienen misa que aún puedes alcanzar hoy; si hoy ya no queda ninguna, entre todas
  const hoy=arr.filter(x=>x.m.k===0), pool=hoy.length?hoy:arr;
  const near=pool.reduce((a,b)=>b.d<a.d?b:a);
  const first=arr.reduce((a,b)=>(b.m.abs<a.m.abs||(b.m.abs===a.m.abs&&b.d<a.d))?b:a);
  return {near,first,sinHoy:!hoy.length};
}
const whenTxt=(m)=>{const dl=m.abs-NOW.min;const w=m.k===0?'Hoy':m.k===1?'Mañana':cap(DOWS[dowOf(m.ds)])+' '+dnum(m.ds);return {a:w+' a las '+m.t,b:dl>0?'en '+dur(dl):'en curso'}};
function heroCard(x,kind,merged,sinHoy){
  const {c,d,e,m}=x, w=whenTxt(m);
  const next=c._u.filter(y=>y!==m&&y.abs>m.abs).slice(0,3).map(y=>whenLabel(y,true)+y.t).join(' · ');
  const k=merged?'La más cercana y la primera en empezar':kind==='near'?(sinHoy?'La más cercana · hoy ya no hay más':'La más cercana con misa hoy'):'La primera que puedes alcanzar';
  return `<div class="best glass on"><div class="ic">${ICON.bell}</div><div><p class="k"><i class="pulse"></i>${k}</p><h2>${esc(c.nombre)}</h2><p><b>${esc(w.a)}</b> (${esc(w.b)}) · ${esc(c.localidad)}</p>${next?`<p>Después: ${esc(next)}</p>`:''}${m.fb?'<p>Horario de la otra temporada (la parroquia no publica el actual).</p>':''}</div>
  <div class="side"><div class="big num">${fmtKm(d)}<small>~${e} min en coche</small></div><div class="acts"><a class="btn guard" href="${route(c)}" target="_blank" rel="noopener">${ICON.go}Cómo llegar</a><button class="btn ghost" type="button" data-open="${c.i}">Ficha</button>${starBtn(c)}</div></div></div>`;
}
function renderBest(){
  const el=$('#best'); const h=heroes();
  let pre='';
  const far=C.length?Math.min(...C.map(c=>c._d)):1e9;
  if(LOADING)pre=`<div class="info" style="grid-column:1/-1;margin:0"><b>Cargando las iglesias de tu zona…</b></div>`;
  else if(far>30){const ds=IDX.dioc.map(d=>d.nombre).join(', ');pre=`<div class="info warn" style="grid-column:1/-1;margin:0"><b>Aún no tengo horarios oficiales de esta zona</b>Por ahora cubro las diócesis de ${esc(ds)}${far<1e8?`; la iglesia más cercana que conozco está a ${fmtKm(far)}`:''}. Voy añadiendo más diócesis (mira «Fuentes»).</div>`}
  if(far>80&&!LOADING){el.innerHTML=pre;return}
  if(!h){el.innerHTML=pre+`<div class="best glass"><div class="ic mut">${ICON.bell}</div><div><p class="k mut">Sin misas próximas</p><h2>No encuentro misas en los próximos 8 días</h2><p>Puede que las parroquias no publiquen horario. Mira la lista y llama antes de ir.</p></div></div>`;return}
  const same=h.near.c===h.first.c&&h.near.m===h.first.m;
  el.innerHTML=pre+(same?heroCard(h.near,'near',true,h.sinHoy):heroCard(h.near,'near',false,h.sinHoy)+heroCard(h.first,'first'));
}

// ---------- lista ----------
const FL=[['todas','Todas'],['hoy','Hoy'],['en','En inglés'],['fav','Favoritas']];
function renderList(){
  const st=$('#status'), li=$('#list');
  const all=sorted();
  const hoy=ROWS.filter(c=>c._u&&c._u[0]&&c._u[0].k===0).length;
  st.innerHTML=`<span><span class="count num">${nf.format(ROWS.length)}</span> iglesias a menos de ${RAD} km${LOC.def?' de Sotogrande':''}</span>`+
    FL.map(([k,t])=>`<button type="button" class="qchip" data-f="${k}" aria-pressed="${FILT===k}">${t}${k==='hoy'?` <span class="n">${hoy}</span>`:''}${k==='fav'?` <span class="n">${ROWS.filter(isFav).length}</span>`:''}</button>`).join('')+
    `<span style="flex:1"></span><button type="button" class="qchip" data-o="${ORD==='cerca'?'antes':'cerca'}" title="Cambiar el orden de la lista">Orden: ${ORD==='cerca'?'más cercana':'antes empieza'}</button>`;
  if(!all.length){li.innerHTML=`<div class="empty"><b>Nada con este filtro</b>${FILT==='fav'?'Marca iglesias con la estrella para verlas aquí.':'Prueba a ampliar el radio o quitar el filtro.'}</div>`;return}
  li.innerHTML=all.map(c=>{const s=c._s;return `<div class="row${s.k==='pronto'||s.k==='curso'?' g':''}" role="button" tabindex="0" data-sel="${c.i}" aria-selected="${SEL===c.i}"><i class="dot s-${s.k}"></i><span class="t"><b>${esc(c.nombre)} ${langBadge(c)}</b><span>${esc(c.localidad)}${c.aprox?' · ubicación aproximada':''}</span></span><span class="km num">${fmtKm(c._d)}</span><span class="st s-${s.k}">${esc(s.t)}<small>${esc(s.d)}</small></span>${starBtn(c)}</div>`}).join('');
}
$('#status').addEventListener('click',e=>{const b=e.target.closest('[data-f]');if(b){FILT=b.dataset.f;LS.set('filt',FILT);renderList();MAP.draw();return}const o=e.target.closest('[data-o]');if(o){ORD=o.dataset.o;LS.set('ord',ORD);renderList()}});
$('#list').addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('.row')){e.preventDefault();select(+e.target.dataset.sel,true)}});

document.addEventListener('click',e=>{
  const f=e.target.closest('[data-fav]'); if(f){e.preventDefault();toggleFav(+f.dataset.fav);return}
  const o=e.target.closest('[data-open],[data-sel]'); if(o&&!e.target.closest('a')){select(+(o.dataset.open??o.dataset.sel),true)}
  if(e.target.id==='cx'){SEL=null;render()}
  const sb=e.target.closest('[data-seas]'); if(sb){SEAS=sb.dataset.seas;renderCard()}
});
function select(i,pan){
  SEL=i; const c=C[i]; SEAS=null; if(VIEW!=='cerca'){location.hash='cerca'}
  render(); if(pan)MAP.focus(c.lat,c.lon);
  if(innerWidth<900)$('.mapbox').scrollIntoView({behavior:'smooth',block:'start'});
}

// ---------- ficha ----------
function weekTable(c,sk){
  const h=c.h[sk]; if(emptySeason(h))return '<p class="note">Sin horario publicado para esta temporada.</p>';
  const today=dowOf(NOW.date), kind=kindOf(NOW.date), curS=seasonOf(c,NOW.date).s;
  const cell=a=>a&&a.length?a.map(t=>`<span>${t}</span>`).join(''):'<span>—</span>';
  const lab=h.lab; const same=lab.every(l=>l.join()===lab[0].join());
  const rows=[];
  const on=(w)=>sk===curS&&kind==='lab'&&today===w;
  if(same)rows.push(['Lunes a viernes',lab[0],sk===curS&&kind==='lab']);
  else lab.forEach((l,w)=>rows.push([cap(DOWS[w]),l,on(w)]));
  rows.push(['Sábado (víspera)',h.visp,sk===curS&&kind==='visp']);
  rows.push(['Domingo y festivos',h.fest,sk===curS&&kind==='fest']);
  return `<table class="wtab">${rows.map(([n,a,hoy])=>`<tr class="${hoy?'hoy':''}"><th>${n}</th><td>${cell(a)}</td></tr>`).join('')}</table>`;
}
function renderCard(){
  const el=$('#card'); if(SEL===null){el.hidden=true;return}
  const c=C[SEL], s=c._s||status(c), d=distKm(LOC.lat,LOC.lon,c.lat,c.lon);
  const cur=seasonOf(c,NOW.date).s, sk=SEAS||cur;
  const up=(c._u||[]).slice(0,4).map(m=>esc(cap((m.k===0?'hoy':m.k===1?'mañana':DOWS[dowOf(m.ds)]+' '+dnum(m.ds))+' '+m.t))).join('<br>');
  const hasBoth=!emptySeason(c.h.inv)&&!emptySeason(c.h.ver)&&JSON.stringify(c.h.inv)!==JSON.stringify(c.h.ver);
  el.hidden=false;
  el.innerHTML=`<button class="x" type="button" id="cx" aria-label="Cerrar">×</button><h3>${esc(c.nombre)} ${langBadge(c)}</h3><p class="sub">${esc(c.addr)} · ${esc(c.diocesis)}</p>
  <div class="facts"><div class="fact ${s.k==='pronto'||s.k==='curso'?'g':''}"><span>Próxima misa</span><b class="s-${s.k}">${esc(s.t)}${s.d?' · '+esc(s.d):''}</b></div><div class="fact"><span>Distancia</span><b class="num">${fmtKm(d)} · ~${eta(d)} min</b></div>
  ${up?`<div class="fact wide"><span>Siguientes misas</span><b>${up}</b></div>`:''}
  ${c.tel?`<div class="fact"><span>Teléfono</span><b class="num">${esc(telFmt(c.tel))}</b></div>`:''}${c.parroco?`<div class="fact"><span>${esc(c.rol||'Párroco')}</span><b>${esc(c.parroco)}</b></div>`:''}</div>
  <div class="cacts"><a class="btn guard" href="${route(c)}" target="_blank" rel="noopener">${ICON.go}Cómo llegar</a>${c.tel?`<a class="btn ghost" href="tel:${esc(c.tel.replace(/\D/g,''))}">${ICON.tel}Llamar</a>`:''}<a class="btn ghost" href="${esc(c.url)}" target="_blank" rel="noopener">${ICON.ext}Fuente</a>${starBtn(c)}</div>
  <h3 class="sub2" style="margin:16px 0 4px;font-size:15px">Horario semanal</h3>
  ${hasBoth?`<div class="seas"><button type="button" data-seas="inv" aria-pressed="${sk==='inv'}">Invierno${cur==='inv'?' · ahora':''}</button><button type="button" data-seas="ver" aria-pressed="${sk==='ver'}">Verano${cur==='ver'?' · ahora':''}</button></div>`:''}
  ${weekTable(c,hasBoth?sk:(emptySeason(c.h.inv)?'ver':'inv'))}
  ${c.obs?`<p class="note"><b>Observaciones de la parroquia:</b> ${esc(c.obs)}</p>`:''}
  ${c.texto?`<details class="note"><summary>Texto original publicado</summary><p>${esc(c.texto)}</p></details>`:''}
  ${!c.interpretado?'<p class="note"><b>No he podido interpretar el horario.</b> Consulta la fuente oficial o llama a la parroquia.</p>':''}
  ${c.id.startsWith('m')&&c.interpretado?'<p class="note">Horario interpretado automáticamente desde un texto libre de la diócesis. Si algo no cuadra, manda el texto original que aparece arriba.</p>':''}
  ${c.res?'<p class="note"><b>Capilla de una residencia de mayores.</b> Confirma con la parroquia si se puede asistir sin ser residente.</p>':''}
  ${c.aprox?'<p class="note">La ubicación en el mapa es aproximada (se ha situado por la localidad o la calle).</p>':''}
  ${s.k!=='nd'&&c._u&&c._u[0]&&c._u[0].fb?'<p class="note">La parroquia no publica horario de esta temporada: se muestra el de la otra.</p>':''}
  <p class="note">Fuente: ${esc(c.fuente)}${c.actualizado?' · actualizado '+esc(c.actualizado.slice(0,10).split('-').reverse().join('/')):''}. Los festivos y vísperas de festivo pueden tener horarios distintos.</p>`;
}

// ---------- mapa vectorial ----------
const MAP=(function(){
  const box=$('#map'), svg=$('#msvg');
  let cLat=DEFLOC.lat,cLon=DEFLOC.lon,ppk=6,inited=false,W=0,H=0;
  const KM=111.32;
  const proj=(lat,lon)=>[W/2+(lon-cLon)*KM*Math.cos(cLat*Math.PI/180)*ppk, H/2-(lat-cLat)*KM*ppk];
  const unproj=(x,y)=>[cLat-(y-H/2)/(KM*ppk), cLon+(x-W/2)/(KM*Math.cos(cLat*Math.PI/180)*ppk)];
  const RINGS=GEO.map(g=>({b:g.b,r:g.r.map(s=>s.split(' ').map(p=>p.split(',').map(Number)))}));
  function size(){const r=box.getBoundingClientRect();W=r.width;H=r.height;svg.setAttribute('viewBox',`0 0 ${W} ${H}`)}
  function draw(){
    if(!W)size(); if(!W)return;
    const [n,w]=unproj(0,0),[s,e]=unproj(W,H), out=[], km=W/ppk;
    RINGS.forEach(g=>{
      if(g.b[0]>e||g.b[2]<w||g.b[1]>n||g.b[3]<s)return;
      out.push(`<path class="land" d="${g.r.map(r=>'M'+r.map(([x,y])=>proj(y,x).map(z=>z.toFixed(1)).join(',')).join('L')+'Z').join('')}"/>`);
    });
    if(LOC){const[x,y]=proj(LOC.lat,LOC.lon);[1,2,5,10,25,50].forEach(r=>{const rp=r*ppk;if(rp<28||rp>Math.max(W,H)*1.2)return;out.push(`<circle class="ring" cx="${x}" cy="${y}" r="${rp}"/><text class="rl" x="${x+rp*0.707+4}" y="${y-rp*0.707-4}">${r} km</text>`)})}
    // lugares
    const used=[]; let nl=0;
    for(const p of PLACES.slice().sort((a,b)=>b.c-a.c)){
      if(p.lat>n||p.lat<s||p.lon<w||p.lon>e)continue;
      const[x,y]=proj(p.lat,p.lon); if(used.some(([a,b])=>Math.abs(a-x)<90&&Math.abs(b-y)<18))continue; used.push([x,y]);
      out.push(`<text class="pl${p.c>2?' big':''}" x="${x}" y="${y}" text-anchor="middle">${esc(p.n)}</text>`); if(++nl>=30)break;
    }
    // iglesias
    const r=km<8?8:km<25?6.5:km<70?5:3.2;
    const hs=heroSet();
    const items=C.filter(c=>c.lat<=n&&c.lat>=s&&c.lon>=w&&c.lon<=e&&(FILT==='todas'||passes(c)||c.i===SEL)).map(c=>[{curso:5,pronto:5,hoy:3,luego:2,nd:1}[c._s.k]+(c.i===SEL?10:0),c]);
    items.sort((a,b)=>a[0]-b[0]);
    for(const[,c]of items){
      const[x,y]=proj(c.lat,c.lon), big=(c.i===SEL||hs.has(c.i))?r+2.5:r, k=c._s.k;
      out.push(`<g class="ph s-${k}${c.i===SEL?' sel':''}${isFav(c)?' fav':''}" data-sel="${c.i}"><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${big}"/>${big>=8?`<path class="cross" transform="translate(${(x-big*.5).toFixed(1)} ${(y-big*.5).toFixed(1)}) scale(${(big/24).toFixed(3)})" d="M9.2 4h5.6v5.2H20v5.6h-5.2V20H9.2v-5.2H4V9.2h5.2z"/>`:''}<title>${esc(c.nombre)} · ${esc(c._s.t)}</title></g>`);
      if((hs.has(c.i)||c.i===SEL)&&km<60)out.push(`<text class="gl" x="${(x+big+5).toFixed(1)}" y="${(y+4).toFixed(1)}">${esc(c.nombre.replace(/^(Parroquia|Iglesia|Capilla|Santuario)( de| del)?\s*/i,'').slice(0,34))}</text>`);
    }
    if(LOC){const[x,y]=proj(LOC.lat,LOC.lon);out.push(`<g class="me"><circle class="h" cx="${x}" cy="${y}" r="16"/><circle class="c" cx="${x}" cy="${y}" r="7"/></g>`)}
    svg.innerHTML=out.join('');
    const nice=[.1,.2,.5,1,2,5,10,20,50,100].find(k=>k*ppk>=60)||100;
    $('#mscale').textContent=`${nice<1?nice*1000+' m':nice+' km'} ≈ ${Math.round(nice*ppk)} px`;
  }
  function heroSet(){const h=heroes();const s=new Set();if(h){s.add(h.near.c.i);s.add(h.first.c.i)}return s}
  function center(lat,lon,radKm){size();inited=true;cLat=lat;cLon=lon;ppk=Math.min(W,H)/(2.3*Math.max(radKm,1));draw()}
  function focus(lat,lon){cLat=lat;cLon=lon;if(ppk<12)ppk=18;draw()}
  function zoom(k,x,y){x=x??W/2;y=y??H/2;const[la,lo]=unproj(x,y);ppk=Math.max(.5,Math.min(200,ppk*k));const[la2,lo2]=unproj(x,y);cLat+=la-la2;cLon+=lo-lo2;draw()}
  let drag=null,moved=false;
  box.addEventListener('pointerdown',e=>{if(e.target.closest('.mctl'))return;drag={x:e.clientX,y:e.clientY,lat:cLat,lon:cLon};moved=false;box.setPointerCapture(e.pointerId)});
  box.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>4){moved=true;box.classList.add('drag')}
    if(moved){cLat=drag.lat+dy/(KM*ppk);cLon=drag.lon-dx/(KM*Math.cos(cLat*Math.PI/180)*ppk);draw()}});
  const end=e=>{if(!drag)return;box.classList.remove('drag');const was=moved;drag=null;
    if(!was){const g=document.elementFromPoint(e.clientX,e.clientY);const ph=g&&g.closest&&g.closest('.ph');if(ph)select(+ph.dataset.sel,false)}};
  box.addEventListener('pointerup',end);box.addEventListener('pointercancel',()=>{drag=null;box.classList.remove('drag')});
  box.addEventListener('wheel',e=>{e.preventDefault();const r=box.getBoundingClientRect();zoom(e.deltaY<0?1.25:1/1.25,e.clientX-r.left,e.clientY-r.top)},{passive:false});
  $('#zin').addEventListener('click',()=>zoom(1.6));$('#zout').addEventListener('click',()=>zoom(1/1.6));
  $('#zme').addEventListener('click',()=>center(LOC.lat,LOC.lon,RAD));
  new ResizeObserver(()=>{size();if(W&&!inited){inited=true;center(LOC.lat,LOC.lon,RAD)}else draw()}).observe(box);
  return {draw,center,focus};
})();
$('#map').addEventListener('click',e=>{if(e.target.closest('.ph'))e.stopPropagation()},true);

// ---------- semana ----------
function renderWeek(){
  const body=$('#wbody');
  $('#wtitle').textContent='Misas de esta semana cerca de '+(LOC.def?'Sotogrande':LOC.label.replace(/^Tu ubicación · cerca de /,'').split(',')[0]);
  const days=[...Array(7)].map((_,k)=>addDays(NOW.date,k));
  if(!days.includes(WDAY))WDAY=days[0];
  const pool=ROWS.filter(c=>WFILT==='todas'||(WFILT==='en'&&c.en)||(WFILT==='fav'&&isFav(c)));
  const chips=days.map((ds,k)=>{
    const cnt=pool.reduce((a,c)=>a+timesOn(c,ds).t.filter(t=>k>0||tmin(t)>=NOW.min-DUR).length,0);
    return `<button type="button" class="dchip" data-day="${ds}" aria-pressed="${ds===WDAY}"><span>${k===0?'Hoy':k===1?'Mañana':DOWS[dowOf(ds)]}</span><b>${dnum(ds)} ${MES[mnum(ds)-1]}</b><i>${cnt} misa${cnt===1?'':'s'}</i></button>`}).join('');
  const k0=days.indexOf(WDAY);
  const items=[];
  pool.forEach(c=>timesOn(c,WDAY).t.forEach(t=>{if(k0>0||tmin(t)>=NOW.min-DUR)items.push({c,t})}));
  items.sort((a,b)=>a.t.localeCompare(b.t)||a.c._d-b.c._d);
  const wf=[['todas','Todas'],['en','En inglés'],['fav','Favoritas']].map(([k,t])=>`<button type="button" class="qchip" data-wf="${k}" aria-pressed="${WFILT===k}">${t}</button>`).join('');
  const list=items.length?items.map(({c,t})=>{const past=k0===0&&tmin(t)<NOW.min;return `<div class="wrow"><div class="t"><b>${esc(c.nombre)} ${langBadge(c)}</b><span>${esc(c.localidad)} · ${fmtKm(c._d)}${c.tel?' · '+esc(telFmt(c.tel)):''}</span></div><span class="pill${past?' loc':''}">${t}<small>${past?'en curso':kindOf(WDAY)==='fest'?'festivo/domingo':kindOf(WDAY)==='visp'?'víspera':'laborable'}</small></span><span class="km num">${fmtKm(c._d)}</span><span class="acts"><a class="btn guard" href="${route(c)}" target="_blank" rel="noopener">${ICON.go}Ir</a><button class="btn ghost" type="button" data-sel="${c.i}">Ficha</button>${starBtn(c)}</span></div>`}).join('')
    :`<div class="empty"><b>Sin misas este día</b>No hay misas publicadas a menos de ${RAD} km${WFILT!=='todas'?' con este filtro':''}.</div>`;
  body.innerHTML=`<div class="info"><b>Radio de ${RAD} km</b>Todas las misas de las iglesias a menos de ${RAD} km de tu ubicación, ordenadas por hora. Cambia el radio arriba.</div><div class="days">${chips}</div><div class="status" style="margin:8px 0">${wf}</div><div class="wlist glass">${list}</div>`;
}
document.addEventListener('click',e=>{const b=e.target.closest('.dchip');if(b){WDAY=b.dataset.day;renderWeek();return}const f=e.target.closest('[data-wf]');if(f){WFILT=f.dataset.wf;renderWeek()}});

// ---------- favoritas ----------
function renderFavs(){
  const body=$('#fbody'), arr=C.filter(isFav).sort((a,b)=>a._d-b._d);
  const warn=!canSave()&&arr.length?`<div class="info warn"><b>Solo en esta sesión</b>No has aceptado guardar preferencias, así que las favoritas se perderán al cerrar la web. <a href="#" data-cookies>Cambiar</a></div>`:'';
  if(!arr.length){body.innerHTML=`<div class="info"><b>Aún no tienes favoritas</b>Pulsa la estrella de cualquier iglesia para tenerla aquí con su horario de toda la semana.</div>`;return}
  body.innerHTML=warn+arr.map(c=>{const s=c._s,cur=seasonOf(c,NOW.date).s;return `<div class="fav-card glass"><h3><span>${esc(c.nombre)} ${langBadge(c)}</span>${starBtn(c)}</h3><p class="sub">${esc(c.addr)} · ${fmtKm(c._d)} · ~${eta(c._d)} min</p><p><b class="s-${s.k}">${esc(s.t)}${s.d?' · '+esc(s.d):''}</b></p>${weekTable(c,emptySeason(c.h[cur])?(cur==='ver'?'inv':'ver'):cur)}<div class="cacts"><a class="btn guard" href="${route(c)}" target="_blank" rel="noopener">${ICON.go}Cómo llegar</a>${c.tel?`<a class="btn ghost" href="tel:${esc(c.tel.replace(/\D/g,''))}">${ICON.tel}Llamar</a>`:''}<button class="btn ghost" type="button" data-sel="${c.i}">Ver en el mapa</button></div></div>`}).join('');
}

// ---------- fuentes ----------
function renderFuentes(){
  const ok=C.filter(c=>c.interpretado).length, ap=C.filter(c=>c.aprox).length;
  const tot=IDX.dioc.reduce((a,d)=>a+d.n,0), okt=IDX.dioc.reduce((a,d)=>a+d.ok,0);
  $('#method').innerHTML=`<div><h3>Cobertura</h3><p>Solo uso <b>fuentes oficiales de cada diócesis</b>. Ahora mismo: ${IDX.dioc.length} diócesis y ${nf.format(tot)} iglesias y capillas, de las que ${nf.format(okt)} publican un horario que he podido interpretar. España tiene 69 diócesis y unas 23.000 parroquias, y cada una publica a su manera (a veces nada), así que las voy añadiendo de una en una. Si tu zona no está, te lo digo en lugar de inventarlo.</p></div>
  <div><h3>Horarios</h3><p>Salen de las fichas oficiales de cada parroquia. Cádiz, Sevilla y Madrid publican el horario estructurado; Málaga lo publica como texto libre que interpreto automáticamente, por eso muestro también el texto original. Para Guadiaro, Sotogrande y alrededores uso además lo publicado por la parroquia.</p></div>
  <div><h3>Lo que no cubre</h3><p>Misas especiales, bodas y funerales. Festivos locales, vísperas de festivo (solo cuento los sábados), Semana Santa y Navidad. El cambio de horario de verano a invierno varía por parroquia y no siempre está publicado. Si una parroquia cambia hoy su horario, puede tardar días en reflejarse. Ceuta y Gibraltar, de momento, no.</p></div>
  <div><h3>Pendientes de añadir</h3><p>${IDX.pendientes.map(esc).join(' · ')}.</p></div>`;
  $('#cofs').innerHTML=IDX.dioc.map(d=>`<div class="cof glass"><h3>${esc(d.nombre)}<span class="tag on">${d.n}</span></h3><p>${d.ok} con horario · ${d.n-d.ok} sin horario${d.estado!=='ok'?' · <b>datos antiguos</b>':''}</p><a href="${esc(d.web)}" target="_blank" rel="noopener">${esc(d.web.replace(/^https?:\/\/(www\.)?/,'').split('/').slice(0,2).join('/'))}</a></div>`).join('');
}

// ---------- cabecera y pie ----------
function renderKpis(){
  const hoy=C.reduce((a,c)=>a+timesOn(c,NOW.date).t.filter(t=>tmin(t)>=NOW.min-DUR).length,0);
  $('#kpis').innerHTML=`<div class="kpi glass"><b class="num">${nf.format(C.length)}</b><span>iglesias</span></div><div class="kpi glass g"><b class="num">${nf.format(hoy)}</b><span>misas que quedan hoy</span></div><div class="kpi glass"><b class="num">${IDX.dioc.length}</b><span>diócesis cubiertas</span></div>`;
  const b=META.built;
  $('#foot').innerHTML=`Datos: webs oficiales de las diócesis (${esc(IDX.dioc.map(d=>d.nombre).join(', '))}) y parroquia de Guadiaro. Mapa y geocodificación: © colaboradores de OpenStreetMap (ODbL). Actualizado el ${esc(b.slice(8,10)+'/'+b.slice(5,7)+'/'+b.slice(0,4)+' '+b.slice(11))}.${META.fallos&&META.fallos.length?` <b>Aviso:</b> no se pudo actualizar alguna fuente; se muestran los últimos datos válidos.`:''}<nav class="legal"><a href="legal.html#aviso-legal">Aviso legal</a><a href="legal.html#privacidad">Privacidad</a><a href="legal.html#cookies">Cookies</a><a href="legal.html#terminos">Términos de uso</a><a href="legal.html#fuentes">Fuentes y licencias</a><a href="#" data-cookies>Configurar cookies</a></nav><div class="by esc"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="a" d="M3 7c3 0 3 3 6 3s3-3 6-3 3 3 6 3" fill="none" stroke-width="2.4" stroke-linecap="round"/><path class="b" d="M3 14c3 0 3 3 6 3s3-3 6-3 3 3 6 3" fill="none" stroke-width="2.4" stroke-linecap="round"/></svg><span>Un proyecto de <b>esclusa</b></span></div>`;
}

// ---------- render general ----------
function render(){
  compute(); renderQuick();
  if(VIEW==='cerca'){renderBest();renderList();renderCard();MAP.draw()}
  if(VIEW==='semana')renderWeek();
  if(VIEW==='favoritas')renderFavs();
  if(VIEW==='fuentes')renderFuentes();
  renderKpis();
}
const VIEWS=['cerca','semana','favoritas','fuentes'];
function route_(){
  const h=(location.hash||'#cerca').slice(1); VIEW=VIEWS.includes(h)?h:'cerca';
  VIEWS.forEach(v=>$('#v-'+v).hidden=v!==VIEW);
  document.querySelectorAll('.tabs a').forEach(a=>{const on=a.getAttribute('href')==='#'+VIEW;a.classList.toggle('on',on);if(on)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
  const tool=VIEW==='cerca'||VIEW==='semana'; $('#tool').hidden=!tool; $('#quick').hidden=!tool;
  render();
}
addEventListener('hashchange',route_);

// tema
const root=document.documentElement; const th=LS.get('theme'); if(th)root.dataset.theme=th;
$('#theme').addEventListener('click',()=>{const dark=root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;root.dataset.theme=dark?'light':'dark';LS.set('theme',root.dataset.theme)});
// fondo topográfico
(function(){let d='';for(let k=0;k<14;k++){const y=80+k*64;d+=`<path d="M-20 ${y} C 300 ${y-40-k*3} 520 ${y+50} 820 ${y} S 1300 ${y-60} 1620 ${y+10}"/>`}$('#bgTopo').innerHTML=d})();

// ---------- aviso de cookies ----------
const ck=$('#cookies');
function showCookies(cfg){const c=CONSENT();ck.hidden=false;ck.classList.toggle('cfg',!!cfg);$('#ckPref').checked=c?!!c.pref:false}
function closeCookies(){ck.hidden=true}
$('#ckOk').addEventListener('click',()=>{setConsent(true);LS.set('fav',[...FAV]);closeCookies()});
$('#ckNo').addEventListener('click',()=>{setConsent(false);closeCookies()});
$('#ckCfg').addEventListener('click',()=>showCookies(true));
$('#ckSave').addEventListener('click',()=>{const p=$('#ckPref').checked;setConsent(p);if(p)LS.set('fav',[...FAV]);closeCookies()});
document.addEventListener('click',e=>{if(e.target.closest('[data-cookies]')){e.preventDefault();showCookies(true)}});
if(!CONSENT())showCookies(false);

route_();
ensureNear(DEFLOC.lat,DEFLOC.lon,60).then(ch=>{if(ch)render()});
gps(true); // cada vez que entras, intenta situarte
setInterval(()=>{render()},30000);
})();
