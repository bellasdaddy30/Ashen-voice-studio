/* Ashen Voice Studio native workspace v1.3.0
   Whole-book ZIP import, blank-start projects, and chapter-on-demand loading.
   The ZIP is stored locally in IndexedDB; only the selected chapter is expanded into the editor. */
(function(){
  'use strict';

  const NATIVE_VERSION='1.3.0';
  const INIT_KEY='ashen-native-v130-initialized';
  const PROJECT_PREFIX='native-book:';
  const ZIP_PREFIX='native-book-zip:';
  const CHAPTER_PREFIX='native-book-chapter:';
  const isTauri=()=>!!window.__TAURI_INTERNALS__;
  const cleanPath=p=>String(p||'').replace(/\\/g,'/').replace(/^\.\//,'').replace(/^\/+/, '').replace(/\/+/g,'/');
  const dirOf=p=>{p=cleanPath(p);const i=p.lastIndexOf('/');return i<0?'':p.slice(0,i+1)};
  const baseName=p=>cleanPath(p).split('/').pop()||'';
  const projectId=()=>state?.bookProject?.id||'';
  const zipDbKey=id=>ZIP_PREFIX+id;
  const chapterDbKey=(pid,cid)=>CHAPTER_PREFIX+pid+':'+cid;
  let persistTimer=null;

  function makeBlankChapter(){
    return {id:'blank-'+uid(),title:'',lines:[],masterReady:false,loaded:false,projectKey:''};
  }

  function blankState(){
    const chapter=makeBlankChapter();
    return {
      schema:6,
      title:'',
      author:'',
      activeChapterId:chapter.id,
      chapters:[chapter],
      characters:[],
      dictionary:[],
      settings:{dtype:'q4',device:'auto',memorySaver:true,normalize:true,fadeMs:10},
      sources:{productionText:'',manuscriptText:'',pronunciationText:'',guideText:'',names:{}},
      guideNotes:'',
      bookProject:null,
      nativeWorkspace:true,
      updatedAt:Date.now()
    };
  }

  // Make a genuinely new project empty. The legacy migration already falls back
  // through freshState(), so changing this also stops it from resurrecting Narrator.
  freshState=blankState;

  // First native v1.3 launch starts clean, but preserves the old local JSON verbatim.
  const legacyLoadState=loadState;
  loadState=function(){
    if(!localStorage.getItem(INIT_KEY)){
      const old=localStorage.getItem(STORAGE_KEY);
      if(old) localStorage.setItem('ashen-native-v121-backup-'+Date.now(),old);
      localStorage.setItem(INIT_KEY,'1');
      return blankState();
    }
    const s=legacyLoadState();
    s.bookProject=s.bookProject||null;
    s.nativeWorkspace=true;
    return s;
  };

  // Native workspaces are file-driven. Stop the legacy /book-data auto-loader.
  loadRepo=async function(){return false;};

  function zipFiles(zip){return Object.keys(zip.files).filter(k=>!zip.files[k].dir);}

  function findManifestPath(zip){
    const names=zipFiles(zip);
    return names.find(n=>/\bbook-data\/manifest\.json$/i.test(n))
      ||names.find(n=>/^manifest\.json$/i.test(n))
      ||names.find(n=>/\/manifest\.json$/i.test(n))
      ||null;
  }

  function resolveZipPath(zip,root,ref,relativeDir=''){
    if(!ref)return null;
    const r=cleanPath(ref), candidates=[];
    const add=p=>{p=cleanPath(p);if(p&&!candidates.includes(p))candidates.push(p)};
    add(r);
    add(relativeDir+r);
    add(root+r);
    if(/^book-data\//i.test(r)) add(root+r.replace(/^book-data\//i,''));
    for(const c of candidates) if(zip.files[c]&&!zip.files[c].dir)return c;
    const suffix='/'+r;
    const hits=zipFiles(zip).filter(n=>n===r||n.endsWith(suffix));
    return hits.length===1?hits[0]:null;
  }

  async function zipText(zip,path,required=true){
    if(!path){if(required)throw new Error('Required file path is missing');return null;}
    const f=zip.files[path];
    if(!f){if(required)throw new Error(`Missing file in ZIP: ${path}`);return null;}
    return f.async('string');
  }
  async function zipJson(zip,path,required=true){
    const t=await zipText(zip,path,required);
    if(t==null)return null;
    try{return JSON.parse(t)}catch(e){throw new Error(`Invalid JSON in ${path}: ${e.message}`)}
  }

  function manifestChapters(manifest){
    const raw=manifest?.chapters||{};
    if(Array.isArray(raw)) return raw.map((cfg,i)=>[cfg.id||cfg.key||String(i+1),cfg]);
    return Object.entries(raw);
  }

  function displayChapterTitle(key,cfg,i){
    return cfg?.title||cfg?.name||String(key).replace(/^\d+[\-_ ]*/,'').replace(/[\-_]+/g,' ')||`Chapter ${i+1}`;
  }

  async function readCharacters(zip,root,manifest){
    const p=resolveZipPath(zip,root,manifest?.characters||manifest?.characterCards||'',root);
    if(!p)return [];
    const data=await zipJson(zip,p,false);
    const list=Array.isArray(data)?data:(data?.characters||[]);
    return list.filter(c=>c&&c.name).map(makeChar);
  }

  function inferCharactersFromLines(lines){
    if(state.characters.length)return;
    const names=[];
    for(const l of lines||[]){
      const n=String(l.speaker||'').trim();
      if(n&&!names.some(x=>x.toLowerCase()===n.toLowerCase()))names.push(n);
    }
    state.characters=names.map((name,i)=>makeChar({name,voice:name==='Narrator'?'am_michael':VOICES[(i+11)%VOICES.length][0]}));
  }

  async function importBookZip(file){
    if(!file)return;
    if(!window.JSZip)throw new Error('ZIP support is not installed in this native build. Run npm install, then restart cargo tauri dev.');
    setStatus('Reading book ZIP…');
    const zip=await JSZip.loadAsync(file);
    const manifestPath=findManifestPath(zip);
    if(!manifestPath)throw new Error('No manifest.json was found in this ZIP.');
    const root=dirOf(manifestPath);
    const manifest=await zipJson(zip,manifestPath,true);
    const entries=manifestChapters(manifest);
    if(!entries.length)throw new Error('The manifest contains no chapters.');

    const id='book-'+Date.now()+'-'+Math.random().toString(16).slice(2,8);
    const metas=entries.map(([key,cfg],i)=>({
      id:String(cfg?.id||key||i+1),
      key:String(key||cfg?.id||i+1),
      title:displayChapterTitle(key,cfg,i),
      cfg:cfg||{}
    }));

    await dbPut(zipDbKey(id),file);
    const cast=await readCharacters(zip,root,manifest);
    state=blankState();
    state.title=manifest.title||manifest.bookTitle||file.name.replace(/\.zip$/i,'');
    state.author=manifest.author||manifest.byline||'';
    state.characters=cast;
    state.bookProject={
      id,
      source:PROJECT_PREFIX+'zip',
      zipName:file.name,
      manifestPath,
      root,
      manifest,
      chapters:metas,
      importedAt:Date.now()
    };
    state.chapters=metas.map(m=>({id:m.id,title:m.title,lines:[],masterReady:false,loaded:false,projectKey:m.key}));
    state.activeChapterId=state.chapters[0].id;
    state.dictionary=[];
    state.sources={productionText:'',manuscriptText:'',pronunciationText:'',guideText:'',names:{}};
    localStorage.setItem(INIT_KEY,'1');
    save();
    render();
    setStatus(`Book imported · ${metas.length} chapter${metas.length===1?'':'s'} indexed · choose a chapter to load`);
  }

  async function persistActiveChapter(){
    if(!state?.bookProject)return;
    const ch=chapter();
    if(!ch?.loaded)return;
    const snap={
      chapter:clone(ch),
      dictionary:clone(state.dictionary||[]),
      sources:clone(state.sources||{}),
      guideNotes:state.guideNotes||'',
      savedAt:Date.now()
    };
    await dbPut(chapterDbKey(projectId(),ch.id),snap);
  }

  const coreSave=save;
  save=function(){
    coreSave();
    if(persistTimer)clearTimeout(persistTimer);
    persistTimer=setTimeout(()=>persistActiveChapter().catch(e=>console.warn('Chapter persistence skipped',e)),250);
  };

  async function productionLinesFromZip(zip,root,meta){
    const cfg=meta.cfg||{};
    const productionPath=resolveZipPath(zip,root,cfg.production||cfg.productionJson||cfg.data,root);
    if(!productionPath)throw new Error(`No production file is defined for ${meta.title}.`);
    const p=await zipJson(zip,productionPath,true);
    const pc=Array.isArray(p?.chapters)?p.chapters[0]:p;
    let lines=Array.isArray(pc?.lines)?pc.lines:(Array.isArray(p?.lines)?p.lines:[]);
    const lineFiles=pc?.lineFiles||p?.lineFiles;
    if((!lines||!lines.length)&&Array.isArray(lineFiles)&&lineFiles.length){
      const d=dirOf(productionPath);
      const chunks=[];
      for(const ref of lineFiles){
        const lp=resolveZipPath(zip,root,ref,d);
        if(!lp)throw new Error(`Missing chapter segment file: ${ref}`);
        const chunk=await zipJson(zip,lp,true);
        chunks.push(...(Array.isArray(chunk)?chunk:(chunk.lines||[])));
      }
      lines=chunks;
    }
    lines=(lines||[]).map(l=>({
      ...l,
      id:l.id||uid(),
      text:String(l.text||'').trim(),
      speaker:l.speaker||'Narrator',
      type:l.type||((l.speaker&&l.speaker!=='Narrator')?'dialogue':'narration'),
      confidence:l.confidence??1,
      emotion:l.emotion||'neutral',
      pause:l.pause??null,
      note:l.note||'',
      generated:false
    })).filter(l=>l.text);
    return {lines,productionPath,production:p};
  }

  async function readOptionalText(zip,root,ref,base=''){
    const p=resolveZipPath(zip,root,ref,base||root);
    return p?zipText(zip,p,false):null;
  }

  async function loadChapterById(id){
    if(!state?.bookProject)throw new Error('Import a book ZIP first.');
    await persistActiveChapter().catch(()=>{});
    const meta=state.bookProject.chapters.find(x=>String(x.id)===String(id));
    if(!meta)throw new Error('That chapter is not in the imported book.');
    state.activeChapterId=String(meta.id);
    let target=state.chapters.find(c=>String(c.id)===String(meta.id));
    if(!target){target={id:String(meta.id),title:meta.title,lines:[],masterReady:false,loaded:false,projectKey:meta.key};state.chapters.push(target);}

    setStatus(`Loading ${meta.title}…`);
    const saved=await dbGet(chapterDbKey(projectId(),target.id)).catch(()=>null);
    if(saved?.chapter){
      Object.assign(target,saved.chapter,{loaded:true});
      state.dictionary=saved.dictionary||[];
      state.sources=saved.sources||state.sources||{};
      state.guideNotes=saved.guideNotes||'';
      save();
      render();
      if(typeof window.recoverGeneratedAudio==='function')await window.recoverGeneratedAudio().catch(()=>{});
      setStatus(`${target.title} loaded from local project storage`);
      return;
    }

    const blob=await dbGet(zipDbKey(projectId()));
    if(!blob)throw new Error('The locally stored book ZIP could not be found. Re-import the ZIP.');
    const zip=await JSZip.loadAsync(blob);
    const root=state.bookProject.root||dirOf(state.bookProject.manifestPath);
    const {lines,productionPath,production}=await productionLinesFromZip(zip,root,meta);
    target.title=production?.chapters?.[0]?.title||production?.title||meta.title;
    target.lines=lines;
    target.masterReady=false;
    target.loaded=true;

    inferCharactersFromLines(lines);
    const cfg=meta.cfg||{};
    const prodDir=dirOf(productionPath);
    const manuscript=await readOptionalText(zip,root,cfg.manuscript||cfg.text,root);
    const guide=await readOptionalText(zip,root,cfg.guide||cfg.productionGuide,root);
    const globalPron=await readOptionalText(zip,root,state.bookProject.manifest.globalPronunciations||state.bookProject.manifest.pronunciations,root);
    const chapterPron=await readOptionalText(zip,root,cfg.pronunciations,root);
    state.sources={productionText:JSON.stringify(production),manuscriptText:manuscript||'',pronunciationText:[globalPron,chapterPron].filter(Boolean).join('\n'),guideText:guide||'',names:{}};
    state.guideNotes=guide||'';
    state.dictionary=[];
    if(globalPron&&typeof applyPronunciations==='function')applyPronunciations(globalPron);
    if(chapterPron&&typeof applyPronunciations==='function')applyPronunciations(chapterPron);
    if(typeof applyOv==='function')applyOv();
    if(typeof autoDirect==='function')autoDirect(false);
    save();
    await persistActiveChapter();
    render();
    if(typeof window.recoverGeneratedAudio==='function')await window.recoverGeneratedAudio().catch(()=>{});
    setStatus(`${target.title} loaded · ${target.lines.length} production segment${target.lines.length===1?'':'s'} · generation remains chapter-only`);
  }

  async function newBlankProject(){
    await persistActiveChapter().catch(()=>{});
    if(state?.bookProject&&!confirm('Start a new blank project? Your imported ZIP and saved chapter data stay on this computer.'))return;
    state=blankState();
    localStorage.setItem(INIT_KEY,'1');
    save();
    render();
    setStatus('Blank project ready · import a book ZIP when ready');
  }

  function projectPanelHtml(){
    const bp=state.bookProject, metas=bp?.chapters||[];
    const current=state.activeChapterId;
    const ch=chapter();
    return `<div class="sectionHead"><div><h2>Book Project</h2><div class="mini">Import one ZIP for the whole book. The ZIP stays local; chapters are expanded into the editor only when you load them.</div></div><span class="chip">Native v${NATIVE_VERSION}</span></div>
      <div class="nativeProjectGrid">
        <div class="nativeProjectCard"><strong>${bp?esc(state.title||bp.zipName):'No book loaded'}</strong><div class="mini">${bp?`${esc(bp.zipName)} · ${metas.length} chapter${metas.length===1?'':'s'} indexed`:'Character tabs start empty. Import a book ZIP to populate the project.'}</div></div>
        <div class="toolbar nativeProjectActions">
          <label class="btn primary">Import Book ZIP<input id="nativeBookZip" class="hiddenInput" type="file" accept=".zip,application/zip"></label>
          <button id="nativeNewProject" class="btn">New Blank Project</button>
        </div>
      </div>
      ${bp?`<div class="nativeChapterPicker"><div class="field grow"><label>Chapter to work on</label><select id="nativeChapterSelect">${metas.map(m=>`<option value="${esc(m.id)}" ${String(m.id)===String(current)?'selected':''}>${esc(m.title)}</option>`).join('')}</select></div><button id="nativeLoadChapter" class="btn good">Load Selected Chapter</button></div><div class="infoBox">${ch?.loaded?`Loaded now: <b>${esc(ch.title)}</b> · ${ch.lines.length} segments. Generate Missing affects this chapter only.`:'No chapter production data is loaded yet. Choose a chapter and press Load Selected Chapter.'}</div>`:''}
      <div class="progressWrap"><div class="progress"><div id="progressBar"></div></div><div id="progressText" class="progressText">${bp?'Book indexed · waiting for chapter selection':'Waiting for a book ZIP'}</div></div>`;
  }

  function nativeEnhance(){
    const shell=document.querySelector('.shell');
    if(!shell)return;
    document.title=`Ashen Voice Studio Native v${NATIVE_VERSION}`;
    const versionEl=document.querySelector('.version');
    if(versionEl)versionEl.textContent=`v${NATIVE_VERSION} native`;
    const first=[...shell.children].find(x=>x.tagName==='SECTION'&&x.classList.contains('panel'));
    if(first){
      first.classList.add('nativeProjectPanel');
      first.innerHTML=projectPanelHtml();
      const zipInput=byId('nativeBookZip');
      if(zipInput)zipInput.onchange=async e=>{try{await importBookZip(e.target.files?.[0])}catch(err){console.error(err);alert('Book ZIP import failed: '+err.message);setStatus('Book ZIP import failed')}};
      const np=byId('nativeNewProject');if(np)np.onclick=newBlankProject;
      const lc=byId('nativeLoadChapter');if(lc)lc.onclick=async()=>{try{await loadChapterById(byId('nativeChapterSelect')?.value)}catch(err){console.error(err);alert('Chapter load failed: '+err.message);setStatus('Chapter load failed')}};
    }
    byId('repoBox')?.remove();
    const ch=chapter();
    const canGenerate=!!state.bookProject&&!!ch?.loaded&&!!ch.lines?.length;
    ['generateMissing','assemble','clearWavs'].forEach(id=>{const b=byId(id);if(b)b.disabled=!canGenerate});
    const castPanel=[...document.querySelectorAll('section.panel')].find(p=>p.querySelector('h2')?.textContent?.trim()==='Cast');
    if(castPanel&&!state.characters.length){const list=castPanel.querySelector('.castList');if(list)list.innerHTML='<div class="nativeEmptyCast">No characters loaded. Import a book ZIP or add a character manually.</div>'}
  }

  const coreRender=render;
  render=function(){coreRender();nativeEnhance()};

  if(typeof enhance==='function'){
    const legacyEnhance=enhance;
    enhance=function(){legacyEnhance();byId('repoBox')?.remove();nativeEnhance()};
  }

  // Fix the native worker bridge: preserve PCM returned by the worker, support true
  // blend calls, and prefer WASM inside Tauri instead of depending on WebGPU support.
  loadKokoro=async function(){
    if(kokoro&&kokoroWorkerReady)return kokoro;
    if(kokoroLoading)return kokoroLoading;
    kokoroLoading=(async()=>{
      let device=state.settings.device;
      if(isTauri()&&device==='auto')device='wasm';
      else if(device==='auto')device=navigator.gpu?'webgpu':'wasm';
      let dtype=state.settings.memorySaver?'q4':state.settings.dtype;
      if(device==='webgpu'&&dtype==='q4')dtype='q4f16';
      const r=await kokoroWorkerCall('load',{model:KOKORO_MODEL,device,dtype});
      kokoroWorkerReady=true;
      kokoroWorkerConfigKey=`${r.device||device}:${r.dtype||dtype}`;
      const resultAudio=g=>{
        const pcm=new Float32Array(g.pcmBuffer);
        const rate=g.sampleRate||24000;
        return {audio:pcm,data:pcm,sampling_rate:rate,sampleRate:rate,toBlob:async()=>encodeWav(pcm,rate)};
      };
      kokoro={
        generate:async(text,opts={})=>resultAudio(await kokoroWorkerCall('generate',{text,voice:opts.voice,speed:opts.speed||1})),
        generateBlend:async(text,opts={})=>resultAudio(await kokoroWorkerCall('generateBlend',{text,voiceA:opts.voiceA,voiceB:opts.voiceB,weight:opts.weight,speed:opts.speed||1})),
        dispose:async()=>{try{await kokoroWorkerCall('dispose')}catch{}}
      };
      setVoiceBusy(false);
      setEngineProgress(`Voice engine ready · ${r.device||device} ${r.dtype||dtype}`,false);
      return kokoro;
    })();
    try{return await kokoroLoading}catch(e){console.error(e);stopKokoroWorker('Voice engine failed · '+(e?.message||e));throw e}finally{kokoroLoading=null}
  };

  window.AshenNative={importBookZip,loadChapterById,newBlankProject,persistActiveChapter,version:NATIVE_VERSION};
})();
