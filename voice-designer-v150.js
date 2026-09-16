/* Ashen Voice Studio Voice Designer v1.5.0
   Parler-TTS Tiny generates audition voices from descriptions. A chosen candidate
   becomes the permanent LuxTTS master reference for the character. */
(function(){
  'use strict';
  const VERSION='1.5.0';
  const sessions=new Map();

  function invoke(command,args={}){
    const fn=window.__TAURI__?.core?.invoke;
    if(!fn)throw new Error('Tauri native bridge is unavailable. Restart the native desktop app.');
    return fn(command,args);
  }
  function b64Blob(s){
    const bin=atob(s),bytes=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
    return new Blob([bytes],{type:'audio/wav'});
  }
  function choice(id,values,current='unspecified'){
    return `<select id="${id}">${values.map(v=>`<option value="${esc(v)}" ${v===current?'selected':''}>${esc(v)}</option>`).join('')}</select>`;
  }
  function designDefaults(c){
    const d=c.voiceDesign||{};
    return {
      gender:d.gender||'unspecified',
      age:d.age||'unspecified',
      accent:d.accent||c.accent||'unspecified',
      pitch:d.pitch||'unspecified',
      texture:d.texture||c.timbre||'unspecified',
      pace:d.pace||'moderate',
      volume:d.volume||'moderate',
      energy:d.energy||'restrained',
      description:d.description||'',
      sample:d.sample||previewText(c.name),
      count:Number(d.count||2),
      seed:Number(d.seed||4400)
    };
  }
  function readDesignForm(c){
    const d={
      gender:byId('vdGender')?.value||'unspecified',
      age:byId('vdAge')?.value||'unspecified',
      accent:byId('vdAccent')?.value||'unspecified',
      pitch:byId('vdPitch')?.value||'unspecified',
      texture:byId('vdTexture')?.value||'unspecified',
      pace:byId('vdPace')?.value||'moderate',
      volume:byId('vdVolume')?.value||'moderate',
      energy:byId('vdEnergy')?.value||'restrained',
      description:byId('vdDescription')?.value?.trim()||'',
      sample:byId('vdSample')?.value?.trim()||previewText(c.name),
      count:Number(byId('vdCount')?.value||2),
      seed:Number(byId('vdSeed')?.value||4400)
    };
    c.voiceDesign={...(c.voiceDesign||{}),...d};
    save();
    return d;
  }

  function candidateHtml(candidates){
    if(!candidates?.length)return '<div class="mini">No candidates generated yet.</div>';
    return `<div class="designerCandidates">${candidates.map((x,i)=>`<div class="designerCandidate card"><div class="candidateHead"><strong>Candidate ${i+1}</strong><span class="chip">seed ${x.seed}</span></div><audio controls preload="metadata" src="${x.url}"></audio><div class="toolbar"><button class="btn good adoptDesignedVoice" data-index="${i}">Use as Permanent Voice</button></div></div>`).join('')}</div>`;
  }

  async function status(){
    return invoke('native_voice_designer_status');
  }

  function injectDesigner(c){
    const host=byId('nativeEngineFields');
    if(!host||byId('voiceDesignerPanel'))return;
    const d=designDefaults(c);
    const existing=sessions.get(c.id)||[];
    const panel=document.createElement('section');
    panel.id='voiceDesignerPanel';
    panel.className='voiceDesignerPanel';
    panel.innerHTML=`<div class="sectionHead"><div><h3>Voice Designer</h3><div class="mini">Describe an original fictional voice. Parler-TTS Tiny generates audition WAVs; your chosen WAV becomes this character's permanent LuxTTS reference.</div></div><span id="vdStatus" class="chip">checking…</span></div>
      <div class="designerGrid">
        <div class="field"><label>Gender / sex presentation</label>${choice('vdGender',['unspecified','male','female','androgynous'],d.gender)}</div>
        <div class="field"><label>Age</label>${choice('vdAge',['unspecified','teenage','young adult','adult','middle-aged','older adult','elderly'],d.age)}</div>
        <div class="field"><label>Accent</label><input id="vdAccent" value="${esc(d.accent)}" placeholder="American, British, subtle Southern…"></div>
        <div class="field"><label>Pitch</label>${choice('vdPitch',['unspecified','very low','low','low-mid','moderate','high-mid','high','very high'],d.pitch)}</div>
        <div class="field"><label>Texture / timbre</label><input id="vdTexture" value="${esc(d.texture)}" placeholder="gravelly, smooth, brittle, smoky…"></div>
        <div class="field"><label>Speaking rate</label>${choice('vdPace',['very slow','slow','measured','moderate','quick','fast'],d.pace)}</div>
        <div class="field"><label>Volume</label>${choice('vdVolume',['very quiet','quiet','moderate','strong','loud'],d.volume)}</div>
        <div class="field"><label>Energy</label>${choice('vdEnergy',['subdued','restrained','calm','moderate','animated','intense'],d.energy)}</div>
      </div>
      <div class="field"><label>Free-form voice description</label><textarea id="vdDescription" rows="3" placeholder="Weathered, intelligent, dry, speaks as though every word costs him something…">${esc(d.description)}</textarea></div>
      <div class="field"><label>Audition line</label><textarea id="vdSample" rows="3">${esc(d.sample)}</textarea></div>
      <div class="designerGrid compact"><div class="field"><label>Candidates</label>${choice('vdCount',['1','2','3','4'],String(d.count))}</div><div class="field"><label>Starting seed</label><input id="vdSeed" type="number" step="1" value="${d.seed}"></div></div>
      <div class="toolbar"><button id="generateDesignedVoices" class="btn primary">Generate Voice Candidates</button></div>
      <div id="vdProgress" class="infoBox">On Ragnarok, start with 1–2 candidates. This 0.3B designer is much heavier than Kitten/Piper.</div>
      <div id="vdCandidates">${candidateHtml(existing)}</div>`;
    host.insertAdjacentElement('afterend',panel);

    status().then(r=>{
      const s=byId('vdStatus');if(s)s.textContent=r?.available?'Parler Tiny installed':'Parler Tiny not installed';
    }).catch(()=>{const s=byId('vdStatus');if(s)s.textContent='designer unavailable'});

    byId('generateDesignedVoices').onclick=async()=>{
      const btn=byId('generateDesignedVoices');
      try{
        const form=readDesignForm(c);
        btn.disabled=true;
        byId('vdProgress').textContent='Loading Parler-TTS Tiny and designing voices… first use downloads the model and can take a while.';
        setStatus(`Designing ${c.name}'s voice with Parler-TTS Tiny…`);
        const r=await invoke('native_voice_design',{request:{
          text:form.sample,
          description:form.description,
          gender:form.gender,
          age:form.age,
          accent:form.accent,
          pitch:form.pitch,
          texture:form.texture,
          pace:form.pace,
          volume:form.volume,
          energy:form.energy,
          count:form.count,
          seed:form.seed
        }});
        if(!r?.ok)throw new Error(r?.error||'Voice design failed');
        const previous=sessions.get(c.id)||[];
        for(const x of previous)try{URL.revokeObjectURL(x.url)}catch{}
        const candidates=(r.candidates||[]).map(x=>{
          const blob=b64Blob(x.wav_b64);
          const url=URL.createObjectURL(blob);
          objectUrls.push(url);
          return {...x,blob,url};
        });
        sessions.set(c.id,candidates);
        c.voiceDesign={...(c.voiceDesign||{}),resolvedDescription:r.description||form.description,model:r.model};
        save();
        byId('vdProgress').innerHTML=`<b>Generated ${candidates.length} candidate${candidates.length===1?'':'s'}.</b><br><span class="mini">${esc(r.description||'')}</span>`;
        byId('vdCandidates').innerHTML=candidateHtml(candidates);
        wireCandidateButtons(c);
        setStatus(`${c.name} voice candidates ready`);
      }catch(e){
        console.error(e);
        byId('vdProgress').textContent='Voice Designer failed: '+(e?.message||e);
        alert('Voice Designer failed: '+(e?.message||e));
      }finally{btn.disabled=false}
    };
    wireCandidateButtons(c);
  }

  function wireCandidateButtons(c){
    document.querySelectorAll('.adoptDesignedVoice').forEach(b=>b.onclick=async()=>{
      const list=sessions.get(c.id)||[];
      const candidate=list[Number(b.dataset.index)];
      if(!candidate)return;
      try{
        b.disabled=true;
        const name=`designed-${slug(c.name)}-seed-${candidate.seed}.wav`;
        const file=new File([candidate.blob],name,{type:'audio/wav'});
        if(!window.AshenNativeEngines?.saveLuxReference)throw new Error('Lux voice-reference bridge is unavailable.');
        await window.AshenNativeEngines.saveLuxReference(c,file);
        c.engine='lux';
        c.identityLocked=true;
        c.voiceDesign={...(c.voiceDesign||{}),chosenSeed:candidate.seed,chosenFile:name};
        save();
        invalidateSpeaker(c.name);
        setStatus(`${c.name} now uses the designed voice as a locked LuxTTS identity`);
        openVoiceLab(c.id);
      }catch(e){alert('Could not adopt designed voice: '+(e?.message||e))}
      finally{b.disabled=false}
    });
  }

  const previousMakeChar=makeChar;
  makeChar=function(c={}){
    const out=previousMakeChar(c);
    out.voiceDesign=c.voiceDesign||out.voiceDesign||null;
    return out;
  };

  const previousOpenVoiceLab=openVoiceLab;
  openVoiceLab=function(id){
    previousOpenVoiceLab(id);
    const c=state.characters.find(x=>x.id===id)||state.characters[0];
    if(c)injectDesigner(c);
  };

  function enhanceVersion(){
    document.title=`Ashen Voice Studio Native v${VERSION}`;
    const v=document.querySelector('.version');if(v)v.textContent=`v${VERSION} native`;
    const chip=document.querySelector('.nativeProjectPanel .chip');if(chip)chip.textContent=`Native v${VERSION}`;
  }
  const previousRender=render;
  render=function(){previousRender();enhanceVersion()};

  window.AshenVoiceDesigner={version:VERSION,status};
})();
