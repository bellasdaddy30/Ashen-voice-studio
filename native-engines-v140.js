/* Ashen Voice Studio native engines v1.4.0
   Per-character KittenTTS / Piper / LuxTTS routing with a voice identity lock.
   Emotion is performance metadata layered on top of a stable speaker identity. */
(function(){
  'use strict';

  const NATIVE_ENGINE_VERSION='1.4.0';
  const KITTEN_VOICES=['Bella','Jasper','Luna','Bruno','Rosie','Hugo','Kiki','Leo'];
  const KITTEN_MODELS=[
    ['KittenML/kitten-tts-nano-0.8','Nano 0.8 · lightest / best for Ragnarok'],
    ['KittenML/kitten-tts-micro-0.8','Micro 0.8 · higher quality'],
    ['KittenML/kitten-tts-mini-0.8','Mini 0.8 · heaviest Kitten model']
  ];
  const ENGINE_LABELS={kitten:'KittenTTS',piper:'Piper',lux:'LuxTTS'};
  const DELIVERY=['natural','controlled','urgent','clipped','hesitant','soft','commanding'];
  const VOICE_REF_PREFIX='native-voice-ref:';

  function isNative(){return !!window.__TAURI_INTERNALS__||!!window.__TAURI__?.core?.invoke;}
  function invokeNative(command,args={}){
    const invoke=window.__TAURI__?.core?.invoke;
    if(!invoke)throw new Error('Native Tauri voice bridge is unavailable. Restart the native desktop build.');
    return invoke(command,args);
  }
  function engineLabel(id){return ENGINE_LABELS[id]||id||'KittenTTS';}
  function hashName(name){let h=0;for(const ch of String(name||''))h=((h<<5)-h+ch.charCodeAt(0))|0;return Math.abs(h)}
  function defaultKittenVoice(name){
    const fixed={Narrator:'Jasper',Zik:'Hugo',Balag:'Bruno',Enhedu:'Bella',Ninsun:'Luna','Bel-iddin':'Leo','Dead King':'Bruno'};
    return fixed[name]||KITTEN_VOICES[hashName(name)%KITTEN_VOICES.length];
  }

  const coreMakeChar=makeChar;
  makeChar=function(c={}){
    const out=coreMakeChar(c);
    const requested=String(c.engine||c.nativeEngine||'').toLowerCase();
    out.engine=['kitten','piper','lux'].includes(requested)?requested:(c.mode==='clone'&&c.cloneReady?'lux':'kitten');
    out.engineModel=c.engineModel||(out.engine==='kitten'?'KittenML/kitten-tts-nano-0.8':out.engine==='lux'?'YatharthS/LuxTTS':'');
    out.engineVoice=c.engineVoice||c.nativeVoice||(out.engine==='piper'?'en_US-lessac-medium':defaultKittenVoice(out.name));
    out.identityLocked=c.identityLocked!==false;
    out.cadence=c.cadence||'natural';
    out.accent=c.accent||'';
    out.timbre=c.timbre||'';
    out.emotionIntensity=Math.max(0,Math.min(1,Number(c.emotionIntensity??.70)));
    out.delivery=c.delivery||'natural';
    out.luxReferenceName=c.luxReferenceName||c.cloneFileName||'';
    out.luxReady=!!(c.luxReady||c.cloneReady);
    out.luxReferenceSynced=!!c.luxReferenceSynced;
    out.luxSteps=Math.max(2,Math.min(8,Number(c.luxSteps??4)));
    out.legacyVoice=c.legacyVoice||c.voice||'';
    return out;
  };

  function augmentState(s){
    if(!s)return s;
    s.schema=Math.max(Number(s.schema||0),7);
    s.settings={
      ...s.settings,
      defaultEngine:s.settings?.defaultEngine||'kitten',
      fallbackEngine:s.settings?.fallbackEngine||'piper',
      identityLockDefault:s.settings?.identityLockDefault!==false
    };
    s.characters=(s.characters||[]).map(makeChar);
    for(const ch of s.chapters||[]){
      for(const l of ch.lines||[]){
        if(l.emotionIntensity==null)l.emotionIntensity=.70;
        if(!l.delivery)l.delivery='natural';
      }
    }
    return s;
  }

  const coreLoadState=loadState;
  loadState=function(){return augmentState(coreLoadState())};
  const coreSave=save;
  save=function(){augmentState(state);return coreSave()};

  function performanceFor(c,emotion,intensity,delivery){
    const em=EMOTIONS[emotion]||EMOTIONS.neutral;
    const amount=Math.max(0,Math.min(1,Number(intensity??c.emotionIntensity??.7)));
    // Identity lock means emotional performance bends around the character's normal
    // pace/cadence instead of replacing the voice recipe.
    let speed=Number(c.speed||.96)*(1+((Number(em.speed||1)-1)*amount));
    const deliverySpeed={natural:1,controlled:.97,urgent:1.05,clipped:1.04,hesitant:.94,soft:.95,commanding:1.01}[delivery||'natural']||1;
    speed*=1+((deliverySpeed-1)*amount);
    speed=Math.max(.55,Math.min(1.45,speed));
    const naturalPause=Math.max(0,Number(c.pause??.34));
    const targetPause=Math.max(0,Number(em.pause??naturalPause));
    let pause=naturalPause+(targetPause-naturalPause)*amount;
    const pauseFactor={natural:1,controlled:1.08,urgent:.72,clipped:.65,hesitant:1.35,soft:1.20,commanding:.88}[delivery||'natural']||1;
    pause*=1+((pauseFactor-1)*amount);
    return {speed,pause,emotion:emotion||c.emotion||'neutral',amount,delivery:delivery||'natural'};
  }

  async function blobToBase64(blob){
    const bytes=new Uint8Array(await blob.arrayBuffer());
    let binary='';
    const step=0x8000;
    for(let i=0;i<bytes.length;i+=step)binary+=String.fromCharCode(...bytes.subarray(i,i+step));
    return btoa(binary);
  }
  function base64ToBlob(s,type='audio/wav'){
    const bin=atob(s),bytes=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
    return new Blob([bytes],{type});
  }
  function referenceKey(c){return VOICE_REF_PREFIX+c.id}

  async function saveLuxReference(c,file){
    if(!file)throw new Error('Choose a clean reference recording first.');
    await dbPut(referenceKey(c),file);
    c.engine='lux';
    c.luxReady=true;
    c.luxReferenceName=file.name;
    c.luxReferenceSynced=false;
    save();
    setStatus(`${c.name} reference recording saved locally`);
  }

  async function nativeSynthesize(text,c,perf){
    const engine=c.engine||state.settings.defaultEngine||'kitten';
    const payload={
      op:'synthesize',
      engine,
      text:applyDictionary(text),
      model:c.engineModel||undefined,
      voice:c.engineVoice||undefined,
      speed:perf.speed,
      emotion:perf.emotion,
      emotion_intensity:perf.amount,
      delivery:perf.delivery,
      character_id:c.id,
      lux_steps:c.luxSteps||4
    };

    if(engine==='lux'){
      const ref=await dbGet(referenceKey(c)).catch(()=>null);
      // Send the reference until the native worker has persisted it once. After that,
      // Lux reuses the exact same speaker prompt/identity for every line.
      if(ref&&!c.luxReferenceSynced){
        payload.reference_audio_b64=await blobToBase64(ref);
        payload.reference_name=c.luxReferenceName||ref.name||'reference.wav';
      }else if(!ref&&!c.luxReady){
        throw new Error(`${c.name} needs a LuxTTS reference recording.`);
      }
    }

    setEngineProgress(`Rendering ${c.name} · ${engineLabel(engine)} · ${perf.emotion} ${Math.round(perf.amount*100)}%`,true);
    const r=await invokeNative('native_tts',{request:payload});
    if(!r?.ok)throw new Error(r?.error||'Native voice engine failed');
    if(!r.wav_b64)throw new Error('Native voice engine returned no WAV audio');
    if(engine==='lux'&&!c.luxReferenceSynced){
      const real=state.characters.find(x=>x.id===c.id);
      if(real){real.luxReferenceSynced=true;save()}
    }
    setEngineProgress(`${c.name} rendered · ${engineLabel(engine)}`,false);
    return base64ToBlob(r.wav_b64);
  }

  const webSynthesizeProfile=synthesizeProfile;
  synthesizeProfile=async function(text,c){
    if(!isNative())return webSynthesizeProfile(text,c);
    c=makeChar(c);
    const perf=performanceFor(c,c.emotion,c.emotionIntensity,c.delivery);
    let blob=await nativeSynthesize(text,c,perf);
    // Identity Lock deliberately blocks pitch/timbre-changing post-processing.
    // Unlocking permits the legacy DSP for users who explicitly want it.
    if(!c.identityLocked&&studioProcessingEnabled()){
      const em=EMOTIONS[c.emotion]||EMOTIONS.neutral;
      const pitch=clamp((c.pitch||0)+((em.pitch||0)*perf.amount),-6,6);
      const tone=c.tone==='neutral'?em.tone:c.tone;
      const intensity=clamp((c.intensity||1)*(1+((Number(em.intensity||1)-1)*perf.amount)),.5,1.35);
      blob=await processWav(blob,{pitch,tone,intensity});
    }
    return blob;
  };

  renderLine=async function(l){
    const c=makeChar(clone(charByName(l.speaker)));
    c.emotion=l.emotion||c.emotion||'neutral';
    c.emotionIntensity=l.emotionIntensity??c.emotionIntensity??.7;
    c.delivery=l.delivery||c.delivery||'natural';
    return synthesizeProfile(l.text,c);
  };

  function effectivePause(l){
    const c=makeChar(charByName(l.speaker));
    if(l.pause!=null&&l.pause!=='')return Number(l.pause);
    return performanceFor(c,l.emotion||c.emotion,l.emotionIntensity??c.emotionIntensity,l.delivery||c.delivery).pause;
  }

  assemble=async function(silent=false){
    const blobs=[],pauses=[];
    for(const l of chapter().lines){
      const b=await dbGet(lineKey(l));
      if(!b)continue;
      blobs.push(b);
      pauses.push(effectivePause(l));
    }
    if(!blobs.length){if(!silent)alert('No WAVs generated yet.');return}
    setStatus('Assembling master WAV…');
    const out=await merge(blobs,pauses);
    await dbPut(masterKey(),out);
    chapter().masterReady=blobs.length===chapter().lines.length;
    save();
    if(!silent)render();
    return out;
  };

  profileSummary=function(c){
    c=makeChar(c);
    if(c.engine==='lux')return `${engineLabel(c.engine)} · ${c.luxReferenceName||'reference needed'} · identity ${c.identityLocked?'locked':'unlocked'}`;
    return `${engineLabel(c.engine)} · ${c.engineVoice||'voice'} · ${Number(c.speed||1).toFixed(2)}× · identity ${c.identityLocked?'locked':'unlocked'}`;
  };

  castCard=function(c){
    c=makeChar(c);
    const identity=c.identityLocked?'Identity locked':'Identity unlocked';
    return `<div class="castCard"><div class="castHead"><strong>${esc(c.name)}</strong><span class="chip nativeEngineChip">${esc(engineLabel(c.engine))}</span></div><div class="recipe">${esc(profileSummary(c))}</div><div class="mini identityLine">${esc(identity)} · cadence ${esc(c.cadence||'natural')} · default emotion ${esc(c.emotion||'neutral')}</div><div class="toolbar"><button class="btn tiny editVoice" data-id="${c.id}">Voice Identity</button><button class="btn tiny quickPreview" data-id="${c.id}">Preview</button></div></div>`;
  };

  lineCard=function(l,i){
    const c=makeChar(charByName(l.speaker));
    const e=l.emotion||c.emotion||'neutral';
    const amt=Math.round(100*Number(l.emotionIntensity??c.emotionIntensity??.7));
    const delivery=l.delivery||c.delivery||'natural';
    return `<div class="lineCard ${l.generated?'done':''}" id="line-${l.id}"><div class="lineTop nativeLineTop"><select class="lineSpeaker" data-id="${l.id}">${state.characters.map(x=>`<option ${x.name===l.speaker?'selected':''}>${esc(x.name)}</option>`).join('')}</select><select class="lineEmotion" data-id="${l.id}">${Object.keys(EMOTIONS).map(x=>`<option value="${x}" ${e===x?'selected':''}>${x}</option>`).join('')}</select><select class="lineDelivery" data-id="${l.id}">${DELIVERY.map(x=>`<option value="${x}" ${delivery===x?'selected':''}>${x}</option>`).join('')}</select><label class="emotionStrength" title="Emotion intensity"><span>${amt}%</span><input class="lineEmotionIntensity" data-id="${l.id}" type="range" min="0" max="100" step="5" value="${amt}"></label><input class="linePause speedCell" data-id="${l.id}" type="number" min="0" max="3" step=".05" value="${l.pause??''}" placeholder="auto pause"></div><textarea class="lineText" data-id="${l.id}">${esc(l.text)}</textarea><div class="toolbar"><button class="btn tiny genOne" data-id="${l.id}">${l.generated?'Regenerate':'Generate'} WAV</button><button class="btn tiny previewOne" data-id="${l.id}">Preview</button><span class="chip">#${i+1}</span><span class="chip">${esc(l.type||'segment')}</span><span class="chip">${esc(engineLabel(c.engine))}</span></div><div class="audioRow" id="audio-${l.id}"></div></div>`;
  };

  function engineFields(c){
    if(c.engine==='kitten'){
      return `<div class="voiceGrid"><div class="field"><label>Kitten model</label><select id="nativeModel">${KITTEN_MODELS.map(([id,label])=>`<option value="${id}" ${c.engineModel===id?'selected':''}>${esc(label)}</option>`).join('')}</select></div><div class="field"><label>Kitten voice</label><select id="nativeVoice">${KITTEN_VOICES.map(v=>`<option ${c.engineVoice===v?'selected':''}>${v}</option>`).join('')}</select></div></div><div class="infoBox">The same Kitten voice stays attached to this character. Emotion changes pacing and pauses, not the speaker identity.</div>`;
    }
    if(c.engine==='piper'){
      return `<div class="field"><label>Piper voice model</label><input id="nativeVoice" value="${esc(c.engineVoice||'en_US-lessac-medium')}" placeholder="en_US-lessac-medium"></div><div class="infoBox">Piper is the reliability engine. Emotion only nudges pacing and natural variation inside the same installed voice model.</div>`;
    }
    return `<div class="infoBox"><b>LuxTTS voice clone.</b> One master reference recording defines this character's identity. Every emotional line reuses that same speaker reference.</div><div class="field"><label>Master reference recording</label><input id="luxRefFile" type="file" accept="audio/*,.wav,.mp3,.m4a"></div><div class="mini">${c.luxReady?`Current reference: ${esc(c.luxReferenceName||'saved locally')}`:'No Lux reference saved yet.'}</div><div class="field"><label>Lux sampling steps</label><input id="luxSteps" type="number" min="2" max="8" step="1" value="${c.luxSteps||4}"></div>`;
  }

  openVoiceLab=function(id){
    selectedCharacterId=id;
    const c=makeChar(state.characters.find(x=>x.id===id)||state.characters[0]);
    const original=state.characters.find(x=>x.id===c.id);
    Object.assign(original,c);
    const m=byId('voiceModal');
    m.classList.remove('hidden');
    m.innerHTML=`<div class="modalCard nativeVoiceLab"><div class="sectionHead"><div><h2>Voice Identity · ${esc(c.name)}</h2><div class="mini">Lock who the speaker is. Emotion changes only how that same speaker delivers the line.</div></div><button id="closeVoice" class="btn">Close</button></div>
      <div class="voiceIdentityBanner"><label><input id="identityLocked" type="checkbox" ${c.identityLocked?'checked':''}> <b>Voice Identity Lock</b></label><div class="mini">Keeps the selected voice/clone, accent, base pace, cadence and timbre consistent across emotions.</div></div>
      <div class="voiceGrid"><div class="field"><label>Local engine</label><select id="nativeEngine"><option value="kitten" ${c.engine==='kitten'?'selected':''}>KittenTTS</option><option value="piper" ${c.engine==='piper'?'selected':''}>Piper</option><option value="lux" ${c.engine==='lux'?'selected':''}>LuxTTS · cloned voice</option></select></div><div class="field"><label>Natural speaking speed</label><input id="vSpeed" type="number" min=".55" max="1.45" step=".01" value="${c.speed}"></div><div class="field"><label>Natural pause</label><input id="vPause" type="number" min="0" max="3" step=".05" value="${c.pause}"></div><div class="field"><label>Cadence</label><select id="vCadence">${['natural','deliberate','measured','quick',' clipped','hesitant'].map(x=>x.trim()).map(x=>`<option ${c.cadence===x?'selected':''}>${x}</option>`).join('')}</select></div><div class="field"><label>Accent / dialect note</label><input id="vAccent" value="${esc(c.accent||'')}" placeholder="identity note"></div><div class="field"><label>Timbre / identity note</label><input id="vTimbre" value="${esc(c.timbre||'')}" placeholder="low, dry, warm, brittle…"></div></div>
      <div id="nativeEngineFields">${engineFields(c)}</div>
      <hr style="border:0;border-top:1px solid var(--line);margin:12px 0">
      <div class="sectionHead"><div><h3>Default Performance</h3><div class="mini">Individual dialogue lines can override these without changing the voice identity.</div></div></div>
      <div class="voiceGrid"><div class="field"><label>Default emotion</label><select id="vEmotion">${Object.keys(EMOTIONS).map(x=>`<option ${c.emotion===x?'selected':''}>${x}</option>`).join('')}</select></div><div class="field"><label>Emotion intensity</label><input id="vEmotionIntensity" type="range" min="0" max="100" step="5" value="${Math.round(c.emotionIntensity*100)}"><div id="emotionPct" class="mini">${Math.round(c.emotionIntensity*100)}%</div></div><div class="field"><label>Delivery</label><select id="vDelivery">${DELIVERY.map(x=>`<option ${c.delivery===x?'selected':''}>${x}</option>`).join('')}</select></div></div>
      <div class="field"><label>Consistency preview text</label><textarea id="previewText" rows="3">${esc(previewText(c.name))}</textarea></div>
      <div class="toolbar"><button id="saveNativeVoice" class="btn primary">Save Voice Identity</button><button id="previewNativeVoice" class="btn good">Preview Current Performance</button><select id="consistencyEmotion">${['neutral','tense','angry','fearful','grief','solemn','whispered'].map(x=>`<option>${x}</option>`).join('')}</select><button id="consistencyPreview" class="btn">Test Same Voice + Emotion</button></div><div id="voicePreview" class="preview"></div></div>`;

    function readForm(){
      c.engine=byId('nativeEngine')?.value||c.engine;
      c.identityLocked=!!byId('identityLocked')?.checked;
      c.speed=clamp(byId('vSpeed')?.value??c.speed,.55,1.45);
      c.pause=Math.max(0,Number(byId('vPause')?.value??c.pause));
      c.cadence=byId('vCadence')?.value||c.cadence;
      c.accent=byId('vAccent')?.value||'';
      c.timbre=byId('vTimbre')?.value||'';
      c.emotion=byId('vEmotion')?.value||c.emotion;
      c.emotionIntensity=Math.max(0,Math.min(1,Number(byId('vEmotionIntensity')?.value??70)/100));
      c.delivery=byId('vDelivery')?.value||'natural';
      if(c.engine==='kitten'){
        c.engineModel=byId('nativeModel')?.value||'KittenML/kitten-tts-nano-0.8';
        c.engineVoice=byId('nativeVoice')?.value||defaultKittenVoice(c.name);
      }else if(c.engine==='piper'){
        c.engineModel='';
        c.engineVoice=byId('nativeVoice')?.value||'en_US-lessac-medium';
      }else{
        c.engineModel='YatharthS/LuxTTS';
        c.luxSteps=Math.max(2,Math.min(8,Number(byId('luxSteps')?.value||4)));
      }
      Object.assign(original,c);
      save();
    }

    byId('closeVoice').onclick=()=>m.classList.add('hidden');
    byId('nativeEngine').onchange=e=>{readForm();c.engine=e.target.value;Object.assign(original,c);save();openVoiceLab(c.id)};
    byId('vEmotionIntensity').oninput=e=>{byId('emotionPct').textContent=`${e.target.value}%`};
    if(byId('luxRefFile'))byId('luxRefFile').onchange=async e=>{try{const f=e.target.files?.[0];if(!f)return;await saveLuxReference(c,f);Object.assign(original,c);openVoiceLab(c.id)}catch(err){alert(`Reference save failed: ${err.message}`)}};
    byId('saveNativeVoice').onclick=()=>{readForm();invalidateSpeaker(c.name);m.classList.add('hidden');render()};
    byId('previewNativeVoice').onclick=async()=>{try{readForm();const txt=byId('previewText').value.slice(0,180);setVoiceBusy(true,`Preparing ${c.name} preview…`);const b=await synthesizeProfile(txt,c);await playBlob(b,`${c.name} · ${c.emotion}`)}catch(err){alert(`Preview failed: ${err.message}`)}finally{setVoiceBusy(false)}};
    byId('consistencyPreview').onclick=async()=>{try{readForm();const test=makeChar(clone(c));test.emotion=byId('consistencyEmotion').value;const txt=byId('previewText').value.slice(0,180);setVoiceBusy(true,`Testing ${c.name} · same identity · ${test.emotion}…`);const b=await synthesizeProfile(txt,test);await playBlob(b,`${c.name} · identity locked · ${test.emotion}`)}catch(err){alert(`Consistency preview failed: ${err.message}`)}finally{setVoiceBusy(false)}};
  };

  async function checkNativeEngines(){
    setEngineProgress('Checking local KittenTTS / Piper / LuxTTS…',true);
    try{
      const r=await invokeNative('native_tts',{request:{op:'status'}});
      if(!r?.ok)throw new Error(r?.error||'Native engine check failed');
      const parts=Object.entries(r.engines||{}).map(([id,v])=>`${v.label||engineLabel(id)} ${v.available?'✓':'✗'}`);
      const msg=parts.join(' · ');
      setEngineProgress(msg,false);
      setStatus(msg);
      return r;
    }catch(e){
      setEngineProgress('Native engines unavailable · run the installer once',false);
      setStatus('Native engines unavailable');
      throw e;
    }
  }

  const coreWireNative=wire;
  wire=function(){
    coreWireNative();
    document.querySelectorAll('.lineEmotionIntensity').forEach(x=>x.oninput=e=>{const label=e.target.closest('.emotionStrength')?.querySelector('span');if(label)label.textContent=`${e.target.value}%`});
    document.querySelectorAll('.lineEmotionIntensity').forEach(x=>x.onchange=e=>editLine(e.target.dataset.id,{emotionIntensity:Number(e.target.value)/100},true));
    document.querySelectorAll('.lineDelivery').forEach(x=>x.onchange=e=>editLine(e.target.dataset.id,{delivery:e.target.value},true));
  };

  function nativeEngineEnhance(){
    if(!isNative())return;
    document.title=`Ashen Voice Studio Native v${NATIVE_ENGINE_VERSION}`;
    const versionEl=document.querySelector('.version');if(versionEl)versionEl.textContent=`v${NATIVE_ENGINE_VERSION} native`;
    const projectChip=document.querySelector('.nativeProjectPanel .chip');if(projectChip)projectChip.textContent=`Native v${NATIVE_ENGINE_VERSION}`;
    const dtype=byId('dtype');if(dtype?.closest('.field'))dtype.closest('.field').style.display='none';
    const device=byId('device');if(device?.closest('.field'))device.closest('.field').style.display='none';
    if(byId('toggleMemory'))byId('toggleMemory').style.display='none';
    if(byId('cancelK'))byId('cancelK').style.display='none';
    const load=byId('loadK');if(load){load.textContent='Check Local Engines';load.onclick=()=>checkNativeEngines().catch(e=>alert(e.message))}
    const banner=byId('memoryBanner');if(banner){banner.classList.remove('hidden');banner.textContent='Native voice routing: KittenTTS default · Piper fallback · LuxTTS cloned voices. Voice Identity Lock keeps each speaker consistent across emotions.'}
    const ep=byId('engineProgress');if(ep&&/Voice engine not loaded|Kokoro/i.test(ep.textContent))ep.textContent='Local engines not checked yet · KittenTTS / Piper / LuxTTS';
    const open=byId('openVoices');if(open)open.textContent='Configure Voice Identities';
    const mobile=byId('mobileVoices');if(mobile)mobile.textContent='Voices';
    const castPanel=[...document.querySelectorAll('section.panel')].find(p=>p.querySelector('h2')?.textContent?.trim()==='Cast');
    const castMini=castPanel?.querySelector('.sectionHead .mini');if(castMini)castMini.textContent='Each character owns one stable voice identity. Emotion is applied per line without changing who is speaking.';
  }

  const renderBeforeNativeEngines=render;
  render=function(){renderBeforeNativeEngines();nativeEngineEnhance()};

  window.AshenNativeEngines={
    version:NATIVE_ENGINE_VERSION,
    check:checkNativeEngines,
    performanceFor,
    saveLuxReference,
    engines:ENGINE_LABELS
  };
})();
