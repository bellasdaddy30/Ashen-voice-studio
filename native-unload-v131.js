/* Ashen Voice Studio native workspace v1.3.1 — unload current chapter without deleting it */
(function(){
  'use strict';
  const UNLOADED_ID='__ashen_unloaded_chapter__';
  const delay=ms=>new Promise(r=>setTimeout(r,ms));

  async function unloadCurrentChapter(){
    try{
      const current=typeof chapter==='function'?chapter():null;
      if(current?.loaded){
        // v1.3 save() schedules the current chapter snapshot into IndexedDB.
        // Give that debounce time to finish before changing activeChapterId.
        save();
        setStatus('Saving current chapter before unloading…');
        await delay(450);
      }

      const placeholder={
        id:UNLOADED_ID,
        title:'',
        lines:[],
        masterReady:false,
        loaded:false,
        projectKey:''
      };
      state.chapters=(state.chapters||[]).filter(c=>c.id!==UNLOADED_ID);
      state.chapters.unshift(placeholder);
      state.activeChapterId=UNLOADED_ID;
      state.dictionary=[];
      state.sources={productionText:'',manuscriptText:'',pronunciationText:'',guideText:'',names:{}};
      state.guideNotes='';
      save();
      render();
      setStatus('Chapter unloaded from the workspace · saved chapter data and generated audio were not deleted');
    }catch(e){
      console.error(e);
      alert('Could not unload chapter: '+(e?.message||e));
    }
  }

  const previousRender=render;
  render=function(){
    previousRender();
    const loadBtn=document.getElementById('nativeLoadChapter');
    if(loadBtn&&!document.getElementById('nativeUnloadChapter')){
      const unload=document.createElement('button');
      unload.id='nativeUnloadChapter';
      unload.className='btn warn';
      unload.textContent='Unload Current Chapter';
      unload.title='Clear the chapter from the editor without deleting its saved work or audio';
      loadBtn.insertAdjacentElement('afterend',unload);
      unload.onclick=unloadCurrentChapter;
    }
  };

  window.unloadAshenChapter=unloadCurrentChapter;
})();
