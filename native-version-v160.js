/* Ashen Voice Studio shared native version marker v1.6.0 */
(function(){
  'use strict';
  const VERSION='1.6.0';
  function enhance(){
    document.title=`Ashen Voice Studio Native v${VERSION}`;
    const v=document.querySelector('.version');if(v)v.textContent=`v${VERSION} native`;
    const chip=document.querySelector('.nativeProjectPanel .chip');if(chip)chip.textContent=`Native v${VERSION}`;
  }
  const previousRender=window.render;
  if(typeof previousRender==='function')window.render=function(){previousRender();enhance()};
  queueMicrotask(enhance);
})();
