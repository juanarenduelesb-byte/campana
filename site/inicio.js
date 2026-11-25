// Cifras de la landing a partir del índice real de datos.
(function(){
  var I=window.CAMPANA_IDX; if(!I||!I.dioc) return;
  var f=function(n){return n.toLocaleString('es-ES')};
  var ok=I.dioc.filter(function(d){return d.n>0});
  var hor=ok.reduce(function(a,d){return a+(d.n||0)},0);
  var osm=(I.osm&&I.osm.n)||0;
  var set=function(id,t){var e=document.getElementById(id); if(e) e.textContent=t};
  set('k-dioc',f(ok.length));
  set('k-hor',f(hor));
  if(hor+osm) set('k-igl',f(Math.floor((hor+osm)/100)*100)+'+');
})();
