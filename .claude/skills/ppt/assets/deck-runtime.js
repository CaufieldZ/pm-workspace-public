/* deck-runtime.js — 纯 deck 范式运行时（蒸馏自 hundsun deck.js）
 * 由 deck-fill.js 注入 <script>，依赖全局 window.__DECK_ACTS__（章节胶囊配置，可空）。
 * 职责：slides 收集 / 页码注入 / ACTS 章节高亮 / progress / 键盘 + 边缘翻页 / fit 缩放。
 */
(function(){
  var slides=[].slice.call(document.querySelectorAll('.slide'));
  var total=slides.length;
  var i=0;
  var curEl=document.getElementById('cur');
  var prog=document.getElementById('progress');
  var totEl=document.getElementById('tot');
  if(totEl) totEl.textContent=total;

  // 页码注入（.pagenum 占位）
  slides.forEach(function(s,k){
    var p=s.querySelector('.pagenum');
    if(p) p.innerHTML='<b>'+String(k+1).padStart(2,'0')+'</b> / '+total;
  });

  // 章节胶囊（ACTS 可空 → 不渲染）
  var ACTS=(window.__DECK_ACTS__&&window.__DECK_ACTS__.length)?window.__DECK_ACTS__:null;
  var actsEl=document.getElementById('acts');
  var actNodes=[];
  if(ACTS&&actsEl){
    actsEl.innerHTML=ACTS.map(function(a){return '<span class="act">'+a.label+'</span>';}).join('');
    actNodes=[].slice.call(actsEl.children);
  }
  function actOf(n){var a=0;if(!ACTS)return 0;for(var k=0;k<ACTS.length;k++){if(n>=ACTS[k].start)a=k;}return a;}

  function show(n){
    i=Math.max(0,Math.min(total-1,n));
    slides.forEach(function(s,k){s.classList.toggle('active',k===i);});
    if(curEl) curEl.textContent=String(i+1).padStart(2,'0');
    if(prog) prog.style.width=((i+1)/total*100)+'%';
    if(ACTS&&actsEl){
      var ai=actOf(i);
      actNodes.forEach(function(el,k){el.classList.toggle('on',k===ai);});
      actsEl.style.display=(i===0)?'none':'flex';
    }
  }
  function next(){show(i+1);}
  function prev(){show(i-1);}
  window.next=next;window.prev=prev;

  document.addEventListener('keydown',function(e){
    if(['ArrowRight','PageDown',' '].indexOf(e.key)>-1){e.preventDefault();next();}
    else if(['ArrowLeft','PageUp'].indexOf(e.key)>-1){e.preventDefault();prev();}
    else if(e.key==='Home'){show(0);}
    else if(e.key==='End'){show(total-1);}
  });

  function fit(){
    var s=Math.min(window.innerWidth/1280,window.innerHeight/720);
    document.getElementById('stage').style.transform='scale('+s+')';
  }
  window.addEventListener('resize',fit);
  fit();show(0);
})();
