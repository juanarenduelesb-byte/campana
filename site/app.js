(function(){
'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const norm=s=>(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const nf=new Intl.NumberFormat('es-ES');
const cap=s=>s.charAt(0).toUpperCase()+s.slice(1);
const pad=n=>String(n).padStart(2,'0');

// ---------- almacenamiento (solo con consentimiento) ----------
const PFX='campana.', PREFS=['theme','fav','rad','filt','ord','ret'];   // el prefijo se mantiene para no perder lo ya guardado
const store=k=>(k==='theme'||k==='fav'||k==='ret')?localStorage:sessionStorage;
function CONSENT(){try{const c=JSON.parse(localStorage.getItem(PFX+'consent'));if(c&&Date.now()-c.t<365*864e5)return c}catch(e){}return null}
function setConsent(pref){try{localStorage.setItem(PFX+'consent',JSON.stringify({pref:!!pref,t:Date.now(),v:1}))}catch(e){}
  if(!pref)PREFS.forEach(k=>{try{localStorage.removeItem(PFX+k);sessionStorage.removeItem(PFX+k)}catch(e){}})}
const canSave=()=>{const c=CONSENT();return !!(c&&c.pref)};
const LS={get(k){try{return JSON.parse(store(k).getItem(PFX+k))}catch(e){return null}},set(k,v){if(!canSave())return;try{store(k).setItem(PFX+k,JSON.stringify(v))}catch(e){}}};

// ---------- datos (un archivo por diócesis, se cargan según dónde estés) ----------
const IDX=window.CAMPANA_IDX, META={built:IDX.built,fallos:IDX.dioc.filter(d=>d.estado!=='ok')};
const C=[], PLACES=[], LOADED=new Set(); let LOADING=0;
const DEFLOC={lat:40.4168,lon:-3.7038,label:'Madrid',def:true};
const MAIN=['Madrid','Barcelona','Valencia','Sevilla','Zaragoza','Málaga','Bilbao','Granada'];
let NEAR=null; // última posición GPS: los atajos muestran sitios cercanos a ella
const BASEPL=[['Sotogrande',36.2825,-5.2945],['Gibraltar',36.1408,-5.3536],['Algeciras',36.1408,-5.4562],['La Línea de la Concepción',36.1681,-5.3478],['San Roque',36.2103,-5.3844],['Estepona',36.4276,-5.1459],['Manilva',36.3777,-5.2506],['Casares',36.4459,-5.2736],['Marbella',36.5100,-4.8825],['Tarifa',36.0143,-5.6044],['Los Barrios',36.1856,-5.4912],['Jimena de la Frontera',36.4343,-5.4531],['Castellar de la Frontera',36.2886,-5.4533],['Gaucín',36.5170,-5.3189],
 ['Sevilla',37.3891,-5.9845],['Málaga',36.7213,-4.4214],['Cádiz',36.5271,-6.2886],['Jerez de la Frontera',36.6850,-6.1261],['Córdoba',37.8882,-4.7794],['Granada',37.1773,-3.5986],['Almería',36.8340,-2.4637],['Huelva',37.2614,-6.9447],['Jaén',37.7796,-3.7849],['Madrid',40.4168,-3.7038],['Barcelona',41.3874,2.1686],['Valencia',39.4699,-0.3763],['Zaragoza',41.6488,-0.8891],['Bilbao',43.2630,-2.9350],['Alicante',38.3452,-0.4810],['Murcia',37.9922,-1.1307],['Palma de Mallorca',39.5696,2.6502],['Las Palmas de Gran Canaria',28.1235,-15.4363],['Santa Cruz de Tenerife',28.4636,-16.2518],['Valladolid',41.6523,-4.7245],['Vigo',42.2406,-8.7207],['A Coruña',43.3623,-8.4115],['Santander',43.4623,-3.8100],['Pamplona',42.8125,-1.6458],['San Sebastián',43.3183,-1.9812],['Oviedo',43.3614,-5.8593],['Toledo',39.8628,-4.0273],['Salamanca',40.9701,-5.6635],['Burgos',42.3439,-3.6969],['Logroño',42.4627,-2.4450],['Badajoz',38.8794,-6.9707],['Santiago de Compostela',42.8782,-8.5448]];
function misasOrg(c){return 'https://misas.org/buscar/misas/'+encodeURIComponent((c.localidad||c.nombre).toLowerCase())}
function enrich(c){
  const addr=[c.calle&&(c.calle+(c.num?', '+c.num:'')),c.cp,c.localidad].filter(Boolean).join(', ');
  return {...c,i:C.length,addr,en:(c.idiomas||[]).includes('en'),k:norm(c.nombre+' '+c.localidad)};
}
function rebuildPlaces(){
  const PL={};
  C.forEach(c=>{if(!c.localidad)return;const k=norm(c.localidad);const p=PL[k]||(PL[k]={n:c.localidad,lat:0,lon:0,c:0});p.lat+=c.lat;p.lon+=c.lon;p.c++});
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
  const capas=IDX.dioc.concat(IDX.osm?IDX.osm.capas:[]);
  const need=capas.filter(d=>!LOADED.has(d.id)&&bboxKm(lat,lon,d.bbox)<=(r||60));
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

let kickT=0;function kick(){document.body.classList.add('anim');clearTimeout(kickT);kickT=setTimeout(()=>document.body.classList.remove('anim'),1100)}
// ---------- ubicación ----------
function nearestPlace(lat,lon){let b=null,bd=1e9;PLACES.forEach(p=>{const d=distKm(lat,lon,p.lat,p.lon);if(d<bd){bd=d;b=p}});return {p:b,d:bd}}
function setLoc(l){kick();$('#gmsg').hidden=true;LOC=l; SEL=null; q.value=l.def?'':l.label; MAP.center(l.lat,l.lon,RAD); render(); if(VIEW!=='cerca'&&VIEW!=='semana')location.hash='cerca';
  ensureNear(l.lat,l.lon,Math.max(RAD,25)+25).then(ch=>{if(ch&&LOC===l){SEL=null;render()}})}
function gps(auto){
  const m=$('#gmsg');
  const fail=why=>{
    if(auto){m.hidden=false;m.textContent='No he podido leer tu ubicación'+(why?' ('+why+')':'')+'. Muestro '+DEFLOC.label+'; escribe un lugar o márcalo en el mapa.';}
    else{m.hidden=false;m.textContent='No he podido leer tu ubicación (permiso denegado o no disponible). Escribe tu municipio o toca el botón del mapa para marcar dónde estás.'}
  };
  if(!navigator.geolocation)return fail('no disponible en este navegador');
  if(!auto){m.hidden=false;m.textContent='Pidiendo tu ubicación…'}
  try{
    navigator.geolocation.getCurrentPosition(p=>{
      m.hidden=true; GPSOK=true; NEAR={lat:p.coords.latitude,lon:p.coords.longitude};
      const {p:pl,d}=nearestPlace(p.coords.latitude,p.coords.longitude);
      setLoc({lat:p.coords.latitude,lon:p.coords.longitude,label:d<12&&pl?'Tu ubicación · cerca de '+pl.n:'Tu ubicación',gps:true});
    },err=>fail(err&&err.code===1?'permiso denegado':''),{timeout:9000,maximumAge:60000,enableHighAccuracy:false});
  }catch(e){fail('')}
}
$('#gps').addEventListener('click',()=>gps(false));
const QMAX=()=>innerWidth<600?5:8;
function renderQuick(){
  let arr;
  if(NEAR){ // cerca de tu ubicación: localidades reales (con varias iglesias), sin repetir sitios casi iguales
    const BAD=/^(pp\.|pp |parroquia|centro|hermanas|carmelitas|iglesia|capilla|convento|monasterio|ermita|santuario|bas[ií]lica|colegio|residencia|hospital|real |nuestra|ntra|templo|padres)|[()]/i;
    const dist=p=>distKm(NEAR.lat,NEAR.lon,p.lat,p.lon);
    const pick=(list,max)=>{for(const p of list.sort((a,b)=>dist(a)-dist(b))){if(arr.length>=QMAX())break;if(dist(p)>max)break;if(arr.some(q=>distKm(q.lat,q.lon,p.lat,p.lon)<2.5||q.k.split('/')[0].trim()===p.k.split('/')[0].trim()))continue;arr.push(p)}};
    arr=[]; pick(PLACES.filter(p=>p.c>=2&&!BAD.test(p.n)),50);
    if(arr.length<5)pick(PLACES.filter(p=>!BAD.test(p.n)),150);
  }else arr=MAIN.map(n=>PLACES.find(p=>p.k===norm(n))).filter(Boolean).slice(0,QMAX()+1);
  $('#quick').innerHTML=(NEAR?'<span class="qlab">Cerca de ti:</span>':'')+arr.map(p=>{
    const on=Math.abs(LOC.lat-p.lat)<2e-3&&Math.abs(LOC.lon-p.lon)<2e-3;
    return `<button type="button" class="qchip" data-p="${esc(p.k)}" aria-pressed="${on}">${p.c?'<i class="dot"></i>':''}${esc(p.n.replace(' de la Concepción',''))}</button>`}).join('');
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
  const arr=ROWS.filter(c=>!c.res).map(c=>{const e=eta(c._d);const m=(c._u||[]).find(x=>x.abs-NOW.min>=e-5);return {c,d:c._d,e,m}}).filter(x=>x.m);
  if(!arr.length)return null;
  // la más cercana: entre las que tienen misa que aún puedes alcanzar hoy; si hoy ya no queda ninguna, entre todas
  const hoy=arr.filter(x=>x.m.k===0), pool=hoy.length?hoy:arr;
  const near=pool.reduce((a,b)=>b.d<a.d?b:a);
  const first=arr.reduce((a,b)=>(b.m.abs<a.m.abs||(b.m.abs===a.m.abs&&b.d<a.d))?b:a);
  return {near,first,sinHoy:!hoy.length};
}
const whenTxt=(m)=>{const dl=m.abs-NOW.min;const w=m.k===0?'Hoy':m.k===1?'Mañana':cap(DOWS[dowOf(m.ds)])+' '+dnum(m.ds);return {a:w+' a las '+m.t,b:dl>0?'en '+dur(dl):'en curso'}};
function heroCard(x,kind,merged,sinHoy){
  const {c,d,e,m}=x, dl=m.abs-NOW.min;
  const day=m.k===0?'hoy':m.k===1?'mañana':DOWS[dowOf(m.ds)]+' '+dnum(m.ds);
  const rel=dl>0?'empieza en '+dur(dl):'en curso';
  const next=c._u.filter(y=>y!==m&&y.abs>m.abs).slice(0,3).map(y=>whenLabel(y,true)+y.t).join(' · ');
  const k=merged?'La más cercana y la primera en empezar':kind==='near'?(sinHoy?'La más cercana · hoy ya no hay más':'La más cercana con misa hoy'):'La primera que puedes alcanzar';
  return `<article class="best${kind==='first'?' first':''}${merged?' only':''}"><p class="k"><i class="pulse"></i>${k}</p>
  <div class="when"><span class="hh num">${m.t}</span><span class="day">${esc(day)}</span></div><span class="rel">${esc(rel)}</span>
  <h2>${esc(c.nombre)} ${langBadge(c)}</h2><p class="where">${esc(c.localidad)} · ${fmtKm(d)} · ~${e} min en coche</p>
  ${next?`<p class="after">Después: ${esc(next)}</p>`:''}${m.fb?'<p class="after">Horario de la otra temporada (la parroquia no publica el actual).</p>':''}
  <div class="acts"><a class="btn guard" href="${route(c)}" target="_blank" rel="noopener">${ICON.go}Cómo llegar</a><button class="btn ghost" type="button" data-open="${c.i}">Ver ficha</button>${starBtn(c)}</div></article>`;
}
function renderBest(){
  const el=$('#best'); const h=heroes();
  let pre='';
  const OF=C.filter(c=>!c.osm), far=OF.length?Math.min(...OF.map(c=>c._d)):1e9, hayOsm=C.some(c=>c.osm&&c._d<30);
  if(LOADING)pre=`<div class="info" style="grid-column:1/-1;margin:0"><b>Cargando las iglesias de tu zona…</b></div>`;
  else if(far>30&&hayOsm)pre=`<div class="info warn" style="grid-column:1/-1;margin:0"><b>Aquí aún no tengo horarios oficiales</b>Te enseño las iglesias cercanas (ubicación de OpenStreetMap) y, cuando su ficha colaborativa lo incluye, su horario. En cada una tienes un enlace para consultar el horario en misas.org o en la web de la parroquia.</div>`;
  else if(far>30){const ds=IDX.dioc.map(d=>d.nombre).join(', ');pre=`<div class="info warn" style="grid-column:1/-1;margin:0"><b>Aún no tengo horarios oficiales de esta zona</b>Por ahora cubro las diócesis de ${esc(ds)}. Voy añadiendo más diócesis (mira «Fuentes»).</div>`}
  if(far>80&&!LOADING&&!C.some(c=>c.osm&&c.interpretado&&c._d<30)){el.innerHTML=pre;return}
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
  st.innerHTML=`<span><span class="count num">${nf.format(ROWS.length)}</span> iglesias a menos de ${RAD} km${LOC.def?' de '+DEFLOC.label:''}</span>`+
    FL.map(([k,t])=>`<button type="button" class="qchip" data-f="${k}" aria-pressed="${FILT===k}">${t}${k==='hoy'?` <span class="n">${hoy}</span>`:''}${k==='fav'?` <span class="n">${ROWS.filter(isFav).length}</span>`:''}</button>`).join('')+
    `<span style="flex:1"></span><button type="button" class="qchip" data-o="${ORD==='cerca'?'antes':'cerca'}" title="Cambiar el orden de la lista">Orden: ${ORD==='cerca'?'más cercana':'antes empieza'}</button>`;
  if(!all.length){li.innerHTML=`<div class="empty"><b>Nada con este filtro</b>${FILT==='fav'?'Marca iglesias con la estrella para verlas aquí.':'Prueba a ampliar el radio o quitar el filtro.'}</div>`;return}
  li.innerHTML=all.map(c=>{const s=c._s;return `<div class="row${s.k==='pronto'||s.k==='curso'?' g':''}" role="button" tabindex="0" data-sel="${c.i}" aria-selected="${SEL===c.i}"><i class="dot s-${s.k}"></i><span class="t"><b>${esc(c.nombre)} ${langBadge(c)}</b><span>${esc(c.localidad)}${c.aprox?' · ubicación aproximada':''}</span></span><span class="km num">${fmtKm(c._d)}</span><span class="st s-${s.k}">${esc(s.t)}<small>${esc(s.d)}</small></span>${starBtn(c)}</div>`}).join('');
}
$('#status').addEventListener('click',e=>{const b=e.target.closest('[data-f]');if(b){kick();FILT=b.dataset.f;LS.set('filt',FILT);renderList();MAP.draw();return}const o=e.target.closest('[data-o]');if(o){ORD=o.dataset.o;LS.set('ord',ORD);renderList()}});
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
  el.innerHTML=`<button class="x" type="button" id="cx" aria-label="Cerrar">×</button><h3>${esc(c.nombre)} ${langBadge(c)}</h3><p class="sub">${esc([c.addr,c.diocesis].filter(Boolean).join(" · "))}</p>
  <div class="facts"><div class="fact ${s.k==='pronto'||s.k==='curso'?'g':''}"><span>Próxima misa</span><b class="s-${s.k}">${esc(s.t)}${s.d?' · '+esc(s.d):''}</b></div><div class="fact"><span>Distancia</span><b class="num">${fmtKm(d)} · ~${eta(d)} min</b></div>
  ${up?`<div class="fact wide"><span>Siguientes misas</span><b>${up}</b></div>`:''}
  ${c.tel?`<div class="fact"><span>Teléfono</span><b class="num">${esc(telFmt(c.tel))}</b></div>`:''}${c.parroco?`<div class="fact"><span>${esc(c.rol||'Párroco')}</span><b>${esc(c.parroco)}</b></div>`:''}</div>
  <div class="cacts"><a class="btn guard" href="${route(c)}" target="_blank" rel="noopener">${ICON.go}Cómo llegar</a>${c.tel?`<a class="btn ghost" href="tel:${esc(c.tel.replace(/\D/g,''))}">${ICON.tel}Llamar</a>`:''}<a class="btn ghost" href="${esc(c.url)}" target="_blank" rel="noopener">${ICON.ext}${c.osm?'OpenStreetMap':'Fuente'}</a>${c.web?`<a class="btn ghost" href="${esc(c.web)}" target="_blank" rel="noopener">${ICON.ext}Web</a>`:''}${!c.interpretado||c.osm?`<a class="btn ghost" href="${misasOrg(c)}" target="_blank" rel="noopener">${ICON.ext}Horario en misas.org</a>`:''}${starBtn(c)}</div>
  <h3 class="sub2" style="margin:16px 0 4px;font-size:15px">Horario semanal</h3>
  ${hasBoth?`<div class="seas"><button type="button" data-seas="inv" aria-pressed="${sk==='inv'}">Invierno${cur==='inv'?' · ahora':''}</button><button type="button" data-seas="ver" aria-pressed="${sk==='ver'}">Verano${cur==='ver'?' · ahora':''}</button></div>`:''}
  ${weekTable(c,hasBoth?sk:(emptySeason(c.h.inv)?'ver':'inv'))}
  ${c.obs?`<p class="note"><b>Observaciones de la parroquia:</b> ${esc(c.obs)}</p>`:''}
  ${c.texto?`<details class="note"><summary>Texto original publicado</summary><p>${esc(c.texto)}</p></details>`:''}
  ${c.osm&&!c.interpretado?'<p class="note"><b>No tengo horario oficial de esta iglesia.</b> Su diócesis aún no está incluida. Consulta el horario en misas.org, en la web de la parroquia o llamando.</p>':''}
  ${c.osm&&c.interpretado?'<p class="note"><b>Horario colaborativo de OpenStreetMap</b>, no de la diócesis: compruébalo antes de ir.</p>':''}
  ${!c.osm&&!c.interpretado?'<p class="note"><b>No he podido interpretar el horario.</b> Consulta la fuente oficial o llama a la parroquia.</p>':''}
  ${c.id.startsWith('m')&&c.interpretado?'<p class="note">Horario interpretado automáticamente desde un texto libre de la diócesis. Si algo no cuadra, manda el texto original que aparece arriba.</p>':''}
  ${c.res?'<p class="note"><b>Capilla de una residencia de mayores.</b> Confirma con la parroquia si se puede asistir sin ser residente.</p>':''}
  ${c.aprox?'<p class="note">La ubicación en el mapa es aproximada (se ha situado por la localidad o la calle).</p>':''}
  ${s.k!=='nd'&&c._u&&c._u[0]&&c._u[0].fb?'<p class="note">La parroquia no publica horario de esta temporada: se muestra el de la otra.</p>':''}
  <p class="note">Fuente: ${esc(c.fuente)}${c.actualizado?' · actualizado '+esc(c.actualizado.slice(0,10).split('-').reverse().join('/')):''}. Los festivos y vísperas de festivo pueden tener horarios distintos.</p>`;
}

// ---------- mapa (Leaflet + teselas; si no cargan, siluetas propias) ----------
let PICK=false;
const MAP=(function(){
  const box=$('#map'), el=$('#lmap');
  const m=L.map(el,{zoomControl:false,attributionControl:true,zoomSnap:.25,wheelPxPerZoomLevel:90,scrollWheelZoom:false,fadeAnimation:true,zoomAnimation:true,markerZoomAnimation:true}).setView([DEFLOC.lat,DEFLOC.lon],11);
  m.attributionControl.setPrefix(false);
  m.on('click focus',()=>m.scrollWheelZoom.enable());m.on('mouseout blur',()=>m.scrollWheelZoom.disable());
  L.control.scale({imperial:false,position:'bottomright'}).addTo(m);
  m.createPane('landPane').style.zIndex=150;
  const land=L.layerGroup().addTo(m);
  GEO.forEach(g=>g.r.forEach(r=>L.polygon(r.split(' ').map(p=>{const[x,y]=p.split(',').map(Number);return [y,x]}),{pane:'landPane',className:'land',interactive:false,smoothFactor:1.5}).addTo(land)));
  const dark=()=>{const t=document.documentElement.dataset.theme;return t?t==='dark':matchMedia('(prefers-color-scheme:dark)').matches};
  let tiles=null;
  function setTiles(){
    if(tiles)m.removeLayer(tiles);
    tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(m);
  }
  setTiles();
  new MutationObserver(setTiles).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
  matchMedia('(prefers-color-scheme:dark)').addEventListener('change',setTiles);
  const layer=L.layerGroup().addTo(m);
  function heroSet(){const h=heroes();const s=new Set();if(h){s.add(h.near.c.i);s.add(h.first.c.i)}return s}
  function draw(){
    layer.clearLayers();
    const b=m.getBounds().pad(.25), hs=heroSet(), z=m.getZoom();
    if(z<8.5){ // vista de España: una burbuja por diócesis cubierta
      IDX.dioc.forEach(d=>{
        const la=(d.bbox[0]+d.bbox[2])/2, lo=(d.bbox[1]+d.bbox[3])/2;
        const mk=L.marker([la,lo],{icon:L.divIcon({className:'',html:`<div class="dioc"><b>${esc(d.nombre)}</b> <span>${nf.format(d.n)}</span></div>`,iconSize:[0,0]}),zIndexOffset:d.n,title:d.nombre+': '+d.n+' iglesias',keyboard:true});
        mk.on('click',()=>m.flyToBounds([[d.bbox[0],d.bbox[1]],[d.bbox[2],d.bbox[3]]],{duration:.9,padding:[20,20]}));
        mk.addTo(layer);
      });
      if(LOC)L.marker([LOC.lat,LOC.lon],{icon:L.divIcon({className:'',html:'<div class="me"><i></i></div>',iconSize:[22,22],iconAnchor:[11,11]}),interactive:false,zIndexOffset:9e4}).addTo(layer);
      return;
    }
    if(LOC)L.circle([LOC.lat,LOC.lon],{radius:RAD*1000,className:'ring',interactive:false}).addTo(layer);
    const items=C.filter(c=>c._s&&b.contains([c.lat,c.lon])&&(FILT==='todas'||passes(c)||c.i===SEL)).map(c=>[{curso:5,pronto:5,hoy:3,luego:2,nd:1}[c._s.k]+(c.i===SEL?10:0)+(hs.has(c.i)?6:0),c]);
    items.sort((a,b)=>a[0]-b[0]);
    for(const [w,c] of items){
      const hero=hs.has(c.i), sel=c.i===SEL;
      const mk=L.marker([c.lat,c.lon],{icon:L.divIcon({className:'',html:`<div class="pin s-${c._s.k}${hero?' hero':''}${sel?' sel':''}${isFav(c)?' fav':''}"><i></i></div>`,iconSize:[24,24],iconAnchor:[12,12]}),zIndexOffset:w*100,keyboard:true,title:c.nombre+' · '+c._s.t,riseOnHover:true});
      mk.on('click',()=>{if(PICK)return;select(c.i,false)});
      if((hero||sel)&&z>=10)mk.bindTooltip(esc(c.nombre.replace(/^(Parroquia|Iglesia|Capilla|Santuario)( de| del)?\s*/i,'').slice(0,34))+(c._s.k!=='nd'?` · <span style="color:var(--wine)">${esc(c._s.t)}</span>`:''),{permanent:true,direction:'right',offset:[12,0],className:'tag'});
      mk.addTo(layer);
    }
    if(LOC)L.marker([LOC.lat,LOC.lon],{icon:L.divIcon({className:'',html:'<div class="me"><i></i></div>',iconSize:[22,22],iconAnchor:[11,11]}),interactive:false,zIndexOffset:9e4}).addTo(layer);
  }
  let drawT=0; m.on('moveend zoomend',()=>{clearTimeout(drawT);drawT=setTimeout(()=>{draw();
    if(m.getZoom()>=8.5){const c=m.getCenter(),r=m.getBounds().getNorthEast().distanceTo(c)/1000;ensureNear(c.lat,c.lng,Math.min(r,120)).then(ch=>{if(ch)render()})}},60)});
  $('#zes')&&$('#zes').addEventListener('click',()=>m.flyToBounds([[35.8,-9.4],[43.9,3.4]],{duration:.9}));
  m.on('click',e=>{if(!PICK)return;setPick(false);const {p:pl,d}=nearestPlace(e.latlng.lat,e.latlng.lng);setLoc({lat:e.latlng.lat,lon:e.latlng.lng,label:d<12&&pl?'Punto elegido · cerca de '+pl.n:'Punto elegido en el mapa',pin:true})});
  function center(lat,lon,radKm){m.invalidateSize();m.flyToBounds(L.latLng(lat,lon).toBounds(radKm*2100),{duration:.9,easeLinearity:.2,padding:[20,20]});draw()}
  function focus(lat,lon){m.flyTo([lat,lon],Math.max(m.getZoom(),14),{duration:.9})}
  $('#zin').addEventListener('click',()=>m.zoomIn());$('#zout').addEventListener('click',()=>m.zoomOut());
  $('#zme').addEventListener('click',()=>center(LOC.lat,LOC.lon,RAD));
  new ResizeObserver(()=>m.invalidateSize()).observe(box);
  return {draw,center,focus};
})();
function setPick(on){PICK=on;$('#zpick').setAttribute('aria-pressed',on);$('#map').classList.toggle('picking',on);const h=$('#mhint');h.hidden=!on;if(on)h.textContent='Toca el mapa donde estás'}
$('#zpick').addEventListener('click',()=>setPick(!PICK));

// ---------- semana ----------
function renderWeek(){
  const body=$('#wbody');
  $('#wtitle').textContent='Misas de esta semana cerca de '+(LOC.def?DEFLOC.label:LOC.label.replace(/^Tu ubicación · cerca de /,'').split(',')[0]);
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
  $('#method').innerHTML=`<div><h3>Cobertura</h3><p>Los horarios salen de las <b>webs oficiales de cada diócesis</b>. Ahora mismo: ${IDX.dioc.length} diócesis y ${nf.format(tot)} iglesias y capillas, de las que ${nf.format(okt)} publican un horario que he podido interpretar. España tiene 69 diócesis y unas 23.000 parroquias, y cada una publica a su manera (a veces nada), así que las voy añadiendo de una en una. Si tu zona no está, te lo digo en lugar de inventarlo.</p></div>
  <div><h3>Horarios</h3><p>Salen de las webs oficiales de cada diócesis: buscadores y servicios de datos, tablas, hojas de cálculo o texto libre que interpreto automáticamente. Cuando es texto libre, la ficha muestra también el texto original para que puedas comprobarlo. Algunas diócesis solo publican los horarios de la capital. Para Guadiaro, Sotogrande y alrededores uso además lo publicado por la parroquia.</p></div>
  <div><h3>Lo que no cubre</h3><p>Misas especiales, bodas y funerales. Festivos locales, vísperas de festivo (solo cuento los sábados), Semana Santa y Navidad. El cambio de horario de verano a invierno varía por parroquia y no siempre está publicado. Si una parroquia cambia hoy su horario, puede tardar días en reflejarse. Ceuta y Gibraltar, de momento, no.</p></div>
  ${IDX.osm?`<div><h3>Resto de España</h3><p>Donde aún no hay fuente oficial cargada, el mapa muestra ${nf.format(IDX.osm.n)} iglesias de <b>OpenStreetMap</b> (datos colaborativos, licencia ODbL), de las que ${nf.format(IDX.osm.ok)} tienen un horario aportado por voluntarios; se marca como no oficial. En el resto hay un enlace para consultar el horario en misas.org, que no permite copiar sus datos.</p></div>`:''}<div><h3>Pendientes de añadir</h3><p>${IDX.pendientes.map(esc).join(' · ')}.</p></div>`;
  $('#cofs').innerHTML=IDX.dioc.map(d=>`<div class="cof glass"><h3>${esc(d.nombre)}<span class="tag on">${d.n}</span></h3><p>${d.ok} con horario · ${d.n-d.ok} sin horario${d.estado!=='ok'?' · <b>datos antiguos</b>':''}</p><a href="${esc(d.web)}" target="_blank" rel="noopener">${esc(d.web.replace(/^https?:\/\/(www\.)?/,'').split('/').slice(0,2).join('/'))}</a></div>`).join('');
}

// ---------- cabecera y pie ----------
function renderKpis(){
  const hoy=C.reduce((a,c)=>a+timesOn(c,NOW.date).t.filter(t=>tmin(t)>=NOW.min-DUR).length,0);
  $('#kpis').innerHTML=`<div class="kpi glass"><b class="num">${nf.format(IDX.dioc.reduce((a,d)=>a+d.n,0)+(IDX.osm?IDX.osm.n:0))}</b><span>iglesias en el mapa</span></div><div class="kpi glass g"><b class="num">${nf.format(hoy)}</b><span>misas que quedan hoy en tu zona</span></div><div class="kpi glass"><b class="num">${IDX.dioc.length}</b><span>diócesis cubiertas</span></div>`;
  const b=META.built;
  $('#foot').innerHTML=`Hoy hay misa · Datos: webs oficiales de las diócesis (${esc(IDX.dioc.map(d=>d.nombre).join(', '))}) y parroquia de Guadiaro. Mapa y geocodificación: © colaboradores de OpenStreetMap (ODbL). Actualizado el ${esc(b.slice(8,10)+'/'+b.slice(5,7)+'/'+b.slice(0,4)+' '+b.slice(11))}.${META.fallos&&META.fallos.length?` <b>Aviso:</b> no se pudo actualizar alguna fuente; se muestran los últimos datos válidos.`:''}<nav class="legal"><a href="legal.html#aviso-legal">Aviso legal</a><a href="legal.html#privacidad">Privacidad</a><a href="legal.html#cookies">Cookies</a><a href="legal.html#terminos">Términos de uso</a><a href="legal.html#fuentes">Fuentes y licencias</a><a href="#" data-cookies>Configurar cookies</a></nav><div class="by esc"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="a" d="M3 7c3 0 3 3 6 3s3-3 6-3 3 3 6 3" fill="none" stroke-width="2.4" stroke-linecap="round"/><path class="b" d="M3 14c3 0 3 3 6 3s3-3 6-3 3 3 6 3" fill="none" stroke-width="2.4" stroke-linecap="round"/></svg><span>Un proyecto de <b>esclusa</b></span></div>`;
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
const MISAS=['cerca','semana','favoritas','fuentes'], VIEWS=['inicio'].concat(MISAS,['retiros']); let GPSTRY=false;
function route_(){
  const h=(location.hash||'#inicio').slice(1).split('?')[0]; VIEW=VIEWS.includes(h)?h:(h?'cerca':'inicio');
  const grp=VIEW==='retiros'||VIEW==='inicio'?VIEW:'misas'; document.body.dataset.grp=grp;
  VIEWS.forEach(v=>$('#v-'+v).hidden=v!==VIEW);
  document.querySelectorAll('.tabs a').forEach(a=>{const on=a.dataset.grp?a.dataset.grp===grp:a.getAttribute('href')==='#'+VIEW;a.classList.toggle('on',on);if(on)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
  const tool=VIEW==='cerca'||VIEW==='semana'; $('#tool').hidden=!tool; $('#quick').hidden=!tool;
  if(VIEW==='inicio'){scrollTo(0,0);inicioKpis()}
  if(tool&&!GPSTRY){GPSTRY=true;gps(true)} // la ubicación se pide al entrar en Horarios, no en Inicio
  document.title=VIEW==='inicio'?'Hoy hay misa · La próxima misa, cerca de ti':VIEW==='retiros'?'Retiros (próximamente) · Hoy hay misa':'Hoy hay misa · Horarios de misa cerca de ti';
  if(VIEW==='retiros'){RET.render()}   // sección bloqueada: «Próximamente»
  kick();render();moveInd();
}

function inicioKpis(){
  const f=n=>nf.format(n), ok=IDX.dioc.filter(d=>d.n>0), hor=ok.reduce((a,d)=>a+(d.n||0),0), osm=(IDX.osm&&IDX.osm.n)||0;
  const set=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t};
  set('k-dioc',f(ok.length)); set('k-hor',f(hor)); if(hor+osm)set('k-igl',f(Math.floor((hor+osm)/100)*100)+'+');
}

// ---------- retiros: organizador ----------
const RET=(function(){
  const TIPOS=['Misa','Adoración','Hora santa','Charla','Testimonio','Oración','Laudes','Vísperas','Rosario','Confesiones','Silencio','Grupos','Música','Comida','Cena','Desayuno','Tiempo libre','Llegada','Despedida','Otro'];
  const PLANT={
    hora:{n:'Hora santa (estilo Hakuna)',dias:1,p:[[1,'19:30','Llegada','Acogida'],[1,'20:00','Charla','Charla o testimonio'],[1,'20:30','Adoración','Exposición del Santísimo con música'],[1,'21:30','Oración','Bendición y reserva'],[1,'21:40','Tiempo libre','Algo de picar y tertulia']]},
    dia:{n:'Retiro de un día',dias:1,p:[[1,'10:00','Llegada','Acogida y oración inicial'],[1,'10:30','Charla','Primera meditación'],[1,'11:15','Silencio','Tiempo personal'],[1,'12:30','Confesiones',''],[1,'13:00','Misa',''],[1,'14:00','Comida',''],[1,'15:30','Charla','Segunda meditación'],[1,'16:30','Grupos','Compartir'],[1,'17:30','Adoración','Adoración y bendición'],[1,'18:00','Despedida','']]},
    finde:{n:'Fin de semana (viernes a domingo)',dias:3,p:[[1,'19:00','Llegada',''],[1,'20:30','Cena',''],[1,'21:30','Charla','Apertura del retiro'],[1,'22:30','Oración','Oración de la noche'],[2,'08:30','Laudes',''],[2,'09:00','Desayuno',''],[2,'10:00','Charla',''],[2,'11:00','Silencio',''],[2,'12:30','Misa',''],[2,'14:00','Comida',''],[2,'16:00','Charla',''],[2,'17:00','Grupos',''],[2,'18:30','Confesiones','Confesiones y adoración'],[2,'21:00','Cena',''],[2,'22:00','Música','Velada'],[3,'09:00','Laudes','Laudes y desayuno'],[3,'10:30','Charla','Charla final'],[3,'12:00','Misa','Misa de envío'],[3,'14:00','Despedida','Comida y despedida']]},
    ejer:{n:'Ejercicios en silencio (3 días)',dias:3,p:[[1,'19:00','Llegada','Introducción y comienzo del silencio'],[1,'21:30','Oración',''],[2,'08:00','Laudes',''],[2,'09:30','Charla','Puntos de oración'],[2,'10:00','Silencio','Oración personal'],[2,'12:30','Misa',''],[2,'16:30','Charla','Puntos de oración'],[2,'17:00','Silencio','Oración personal'],[2,'19:00','Confesiones','Acompañamiento personal'],[2,'21:30','Vísperas',''],[3,'08:00','Laudes',''],[3,'09:30','Charla',''],[3,'12:00','Misa','Misa de clausura'],[3,'13:30','Despedida','Se rompe el silencio']]},
  };
  const TAREAS=['Fijar fecha y lugar','Reservar la casa o el espacio','Hablar con el sacerdote (misa y confesiones)','Charlas y testimonios','Música','Comidas','Inscripciones y precio','Autorizaciones de menores y protocolo de protección','Seguro y botiquín','Transporte','Materiales (biblias, cuadernos, folletos)','Avisar a la parroquia'];
  let L=LS.get('ret')||[], cur=L[0]?L[0].id:null;
  const uid=()=>Date.now().toString(36)+Math.random().toString(36).slice(2,6);
  const guarda=()=>{LS.set('ret',L);aviso()};
  function aviso(){const e=$('#rsave');if(!e)return;e.innerHTML=canSave()?'Se guardan solo en este dispositivo.':'Para que no se borren al cerrar la página, <a href="#" id="rck">acepta guardar preferencias</a>. Se quedan solo en este dispositivo.';const a=$('#rck');if(a)a.onclick=ev=>{ev.preventDefault();$('#cookies').hidden=false}}
  function nuevo(pl){
    const r={id:uid(),nombre:'Nuevo retiro',tipo:'',inicio:'',fin:'',lugar:'',personas:'',resp:'',notas:'',prog:[],tareas:TAREAS.map(t=>({t,ok:false}))};
    if(pl)aplica(r,pl);
    L.unshift(r);cur=r.id;guarda();render();
  }
  function aplica(r,k){const P=PLANT[k];r.tipo=P.n;if(r.nombre==='Nuevo retiro')r.nombre=P.n;r.prog=P.p.map(([d,h,a,det])=>({d,h,a,det}))}
  const fmt=d=>d?new Date(d+'T12:00').toLocaleDateString('es-ES',{day:'numeric',month:'short'}):'';
  function dias(r){const n=Math.max(1,...r.prog.map(x=>x.d),1);return n}
  function fechaDia(r,d){if(!r.inicio)return '';const f=new Date(r.inicio+'T12:00');f.setDate(f.getDate()+d-1);return f.toLocaleDateString('es-ES',{weekday:'long',day:'numeric',month:'long'})}
  function render(){
    const lst=$('#rlist'),ed=$('#redit');if(!lst)return;
    lst.innerHTML=L.length?L.map(r=>{const ok=r.tareas.filter(t=>t.ok).length;return `<button type="button" class="ritem${r.id===cur?' on':''}" data-r="${r.id}"><b>${esc(r.nombre)}</b><span>${[fmt(r.inicio),r.lugar].filter(Boolean).map(esc).join(' · ')||'Sin fecha ni lugar'} · ${ok}/${r.tareas.length} tareas</span></button>`}).join(''):'<p class="rempty" style="padding:10px">Aún no tienes ninguno.</p>';
    lst.querySelectorAll('[data-r]').forEach(b=>b.onclick=()=>{cur=b.dataset.r;render()});
    aviso();
    const r=L.find(x=>x.id===cur);
    if(!r){ed.innerHTML=`<div class="rempty"><p><b>Empieza con una plantilla</b> y luego ajústala a tu grupo.</p><div class="plant" style="justify-content:center">${Object.entries(PLANT).map(([k,v])=>`<button type="button" class="chip" data-new="${k}">${esc(v.n)}</button>`).join('')}<button type="button" class="chip" data-new="">En blanco</button></div></div>`;
      ed.querySelectorAll('[data-new]').forEach(b=>b.onclick=()=>nuevo(b.dataset.new||null));renderOrgs();return}
    const n=dias(r), ok=r.tareas.filter(t=>t.ok).length;
    let prog='';
    for(let d=1;d<=n;d++){
      const items=r.prog.map((x,i)=>[x,i]).filter(([x])=>x.d===d).sort((a,b)=>a[0].h.localeCompare(b[0].h));
      prog+=`<div class="dia">${n>1?'Día '+d:'Programa'}${fechaDia(r,d)?' · '+esc(fechaDia(r,d)):''}</div>`+items.map(([x,i])=>`<div class="prog"><input type="time" value="${esc(x.h)}" data-p="${i}" data-k="h" aria-label="Hora"><select data-p="${i}" data-k="a" aria-label="Actividad">${TIPOS.map(t=>`<option${t===x.a?' selected':''}>${t}</option>`).join('')}</select><input class="pdet" type="text" value="${esc(x.det)}" placeholder="Detalle (quién, dónde…)" data-p="${i}" data-k="det"><button class="xb" type="button" data-px="${i}" aria-label="Quitar">×</button></div>`).join('')+`<button type="button" class="chip" data-add="${d}">+ Añadir al ${n>1?'día '+d:'programa'}</button>`;
    }
    const misas=r.prog.filter(x=>x.a==='Misa').length;
    ed.innerHTML=`<div class="rform">
      <label class="w2">Nombre<input type="text" data-f="nombre" value="${esc(r.nombre)}"></label>
      <label>Empieza<input type="date" data-f="inicio" value="${esc(r.inicio)}"></label>
      <label>Termina<input type="date" data-f="fin" value="${esc(r.fin)}"></label>
      <label class="w2">Lugar<input type="text" data-f="lugar" value="${esc(r.lugar)}" placeholder="Casa, parroquia, municipio…"></label>
      <label>Personas<input type="number" min="0" data-f="personas" value="${esc(r.personas)}"></label>
      <label>Responsable<input type="text" data-f="resp" value="${esc(r.resp)}"></label>
      <label class="w4">Notas<textarea data-f="notas" placeholder="Precio, qué llevar, contacto…">${esc(r.notas)}</textarea></label></div>
      <div class="rsec"><h3>Programa</h3><div class="plant">${Object.entries(PLANT).map(([k,v])=>`<button type="button" class="chip" data-pl="${k}" title="Sustituye el programa por la plantilla">${esc(v.n)}</button>`).join('')}<button type="button" class="chip" data-dia="1">+ Día</button></div></div>
      ${prog}
      ${r.lugar?`<p class="note">${misas?'Tu programa tiene '+misas+' misa'+(misas>1?'s':'')+'. ':''}¿Necesitas una misa cerca del lugar? <a href="#" id="rmisa">Ver misas cerca de ${esc(r.lugar)}</a>.</p>`:''}
      <div class="rsec"><h3>Tareas</h3><span class="sub" style="color:var(--muted);font-size:14px">${ok} de ${r.tareas.length} hechas</span></div>
      <div class="rprog"><i style="width:${r.tareas.length?Math.round(ok*100/r.tareas.length):0}%"></i></div>
      ${r.tareas.map((t,i)=>`<div class="tarea${t.ok?' ok':''}"><input type="checkbox" data-t="${i}"${t.ok?' checked':''} aria-label="Hecha"><input type="text" value="${esc(t.t)}" data-tt="${i}" aria-label="Tarea"><button class="xb" type="button" data-tx="${i}" aria-label="Quitar">×</button></div>`).join('')}
      <button type="button" class="chip" id="tadd">+ Añadir tarea</button>
      <div class="racts"><button class="btn soft" type="button" id="rshare">Copiar enlace para compartir</button><button class="btn soft" type="button" id="rprint">Imprimir o guardar PDF</button><button class="btn soft ract-del" type="button" id="rdel">Borrar</button></div>`;
    const upd=fn=>{fn();guarda()};
    ed.querySelectorAll('[data-f]').forEach(el=>el.onchange=()=>upd(()=>{r[el.dataset.f]=el.value;render()}));
    ed.querySelectorAll('[data-p]').forEach(el=>el.onchange=()=>upd(()=>{r.prog[+el.dataset.p][el.dataset.k]=el.value;if(el.dataset.k!=='det')render()}));
    ed.querySelectorAll('[data-px]').forEach(b=>b.onclick=()=>upd(()=>{r.prog.splice(+b.dataset.px,1);render()}));
    ed.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>upd(()=>{const d=+b.dataset.add,u=r.prog.filter(x=>x.d===d).map(x=>x.h).sort().pop()||'10:00';const [hh,mm]=u.split(':').map(Number);const t=Math.min(23,hh+1);r.prog.push({d,h:String(t).padStart(2,'0')+':'+String(mm).padStart(2,'0'),a:'Charla',det:''});render()}));
    ed.querySelectorAll('[data-dia]').forEach(b=>b.onclick=()=>upd(()=>{r.prog.push({d:dias(r)+(r.prog.length?1:0)||1,h:'10:00',a:'Oración',det:''});render()}));
    ed.querySelectorAll('[data-pl]').forEach(b=>b.onclick=()=>{if(r.prog.length&&!confirmar('¿Sustituir el programa actual por la plantilla?'))return;upd(()=>{aplica(r,b.dataset.pl);render()})});
    ed.querySelectorAll('[data-t]').forEach(el=>el.onchange=()=>upd(()=>{r.tareas[+el.dataset.t].ok=el.checked;render()}));
    ed.querySelectorAll('[data-tt]').forEach(el=>el.onchange=()=>upd(()=>{r.tareas[+el.dataset.tt].t=el.value}));
    ed.querySelectorAll('[data-tx]').forEach(b=>b.onclick=()=>upd(()=>{r.tareas.splice(+b.dataset.tx,1);render()}));
    $('#tadd').onclick=()=>upd(()=>{r.tareas.push({t:'Nueva tarea',ok:false});render()});
    $('#rdel').onclick=()=>{if(!confirmar('¿Borrar «'+r.nombre+'»?'))return;L=L.filter(x=>x.id!==r.id);cur=L[0]?L[0].id:null;guarda();render()};
    $('#rprint').onclick=()=>print();
    $('#rshare').onclick=()=>{const u=location.origin+location.pathname+'#retiros?plan='+b64(JSON.stringify({...r,id:undefined}));
      (navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(()=>toast('Enlace copiado: quien lo abra podrá guardar una copia del retiro.'),()=>prompt('Copia este enlace',u))};
    const rm=$('#rmisa'); if(rm)rm.onclick=ev=>{ev.preventDefault();const k=norm(r.lugar);const p=PLACES.find(x=>x.k===k)||PLACES.find(x=>k.includes(x.k)||x.k.includes(k));
      if(p){location.hash='cerca';setLoc({lat:p.lat,lon:p.lon,label:p.n})}else{location.hash='cerca';q.value=r.lugar;q.dispatchEvent(new Event('input'));q.focus()}};
    renderOrgs();
  }
  const b64=t=>btoa(unescape(encodeURIComponent(t))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  const unb64=t=>decodeURIComponent(escape(atob(t.replace(/-/g,'+').replace(/_/g,'/'))));
  function confirmar(m){try{return confirm(m)}catch(e){return true}}
  function importa(){const m=location.hash.match(/plan=([\w-]+)/);if(!m)return;try{const r=JSON.parse(unb64(m[1]));if(r&&r.nombre&&Array.isArray(r.prog)){r.id=uid();r.tareas=Array.isArray(r.tareas)?r.tareas:[];L.unshift(r);cur=r.id;guarda();toast('Retiro «'+esc(r.nombre)+'» añadido a tus retiros.')}}catch(e){}
    history.replaceState(null,'',location.pathname+'#retiros')}
  const ORGS=[
    ['DeRetiro','Buscador de retiros y actividades de parroquias y movimientos de toda España: Emaús, Effetá, Bartimeo, ejercicios, horas santas… por provincia, edad y fecha.','https://deretiro.es/','Buscar retiros',true],
    ['Hakuna','Movimiento de jóvenes con horas santas semanales, retiros (God Stop) y misiones, con su música.','https://hakuna.org/','Ver Hakuna'],
    ['Cursillos de Cristiandad','Movimiento nacido en Mallorca: cursillos de tres días y reuniones de grupo (ultreyas) en casi todas las diócesis.','https://www.cursillosdecristiandad.com/','Ver cursillos'],
    ['Ejercicios espirituales en Manresa','La Cova de Sant Ignasi (jesuitas) organiza ejercicios ignacianos de fin de semana, de ocho días y de un mes.','https://www.covamanresa.cat/','Ver calendario'],
    ['Centro de Espiritualidad de Loyola','Programa anual de ejercicios espirituales de la Compañía de Jesús en el santuario de Loyola (Gipuzkoa).','https://loyola.global/es/','Ver programa'],
    ['Life Teen España','Recursos y encuentros de pastoral juvenil para parroquias: ideas para preparar retiros con adolescentes.','https://www.lifeteen.es/','Ver recursos'],
    ['Proyecto Amor Conyugal','Retiros y materiales para matrimonios.','https://proyectoamorconyugal.es/','Ver retiros'],
  ];
  function renderOrgs(){const o=$('#orgs');if(!o||o.dataset.ok)return;o.dataset.ok=1;
    o.innerHTML=ORGS.map(([n,d,u,l,dest])=>`<div class="org glass${dest?' dest':''}"><h3>${esc(n)}</h3><p>${esc(d)}</p><a href="${u}" target="_blank" rel="noopener">${esc(l)} ↗</a></div>`).join('')+'<p class="note" style="grid-column:1/-1">Enlazamos a webs públicas de cada movimiento; Hoy hay misa no organiza ni avala ninguna actividad.</p>'}
  $('#rnew').onclick=()=>{cur=null;render()};
  return {render,importa};
})();

addEventListener('hashchange',route_);
function moveInd(){document.querySelectorAll('.tabs').forEach(t=>{const a=t.querySelector('a.on'),i=t.querySelector('.pill-ind');if(!a||!i||!a.offsetWidth)return;i.style.width=a.offsetWidth+'px';i.style.transform=`translateX(${a.offsetLeft}px)`})}
addEventListener('resize',moveInd);
if(document.fonts)document.fonts.ready.then(moveInd);
addEventListener('scroll',()=>$('#topnav').classList.toggle('scrolled',scrollY>8),{passive:true});

// tema
const root=document.documentElement; const th=LS.get('theme'); if(th)root.dataset.theme=th;
$('#theme').addEventListener('click',()=>{const dark=root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;root.dataset.theme=dark?'light':'dark';LS.set('theme',root.dataset.theme)});
// fondo topográfico
(function(){let d='';for(let k=0;k<14;k++){const y=80+k*64;d+=`<path d="M-20 ${y} C 300 ${y-40-k*3} 520 ${y+50} 820 ${y} S 1300 ${y-60} 1620 ${y+10}"/>`}const bt=$('#bgTopo');if(bt)bt.innerHTML=d})();

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
setInterval(()=>{render()},30000);
})();
