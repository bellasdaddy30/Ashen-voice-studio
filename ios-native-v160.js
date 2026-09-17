/* Ashen Voice Studio iOS native overlay v1.6.0
   The iPhone build reuses the same book/project UI but routes TTS into Swift + sherpa-onnx.
   Kitten and Piper run locally. The schema's `lux` route is implemented by ZipVoice on iOS. */
(function(){
  'use strict';
  if(!window.AshenIOS)return;

  const VERSION='1.6.0';
  const originalInvoke=window.__TAURI__?.core?.invoke;

  // Keep the existing cross-platform JS contract. On iOS, the native shell supplies
  // a Tauri-shaped invoke bridge so the rest of Ashen Voice does not need a second app UI.
  if(originalInvoke){
    window.__TAURI__.core.invoke=async function(command,args={}){
      if(command==='native_tts'&&args?.request?.engine==='lux'){
        const request={...args.request};
        const c=window.state?.characters?.find?.(x=>String(x.id)===String(request.character_id));
        request.reference_text=c?.cloneReferenceText||c?.luxReferenceText||'';
        request.native_clone_engine='zipvoice';
        args={...args,request};
      }
      return originalInvoke(command,args);
    };
  }

  if(window.AshenNativeEngines?.engines){
    // Same project schema, different native implementation. Desktop `lux` = LuxTTS;
    // iPhone `lux` = ZipVoice zero-shot cloning through sherpa-onnx.
    window.AshenNativeEngines.engines.lux='ZipVoice Clone';
  }

  function currentCharacter(id){
    return window.state?.characters?.find?.(x=>String(x.id)===String(id))||window.state?.characters?.[0]||null;
  }

  function patchVoiceLab(id){
    const c=currentCharacter(id);
    if(!c)return;

    const engineSelect=document.getElementById('nativeEngine');
    if(engineSelect){
      const lux=[...engineSelect.options].find(o=>o.value==='lux');
      if(lux)lux.textContent='ZipVoice · on-device clone';
    }

    const body=document.getElementById('nativeEngineFields');
    if(body&&c.engine==='lux'){
      body.querySelectorAll('.infoBox').forEach(el=>{
        el.innerHTML=el.innerHTML
          .replaceAll('LuxTTS','ZipVoice')
          .replace('One master reference recording defines this character\'s identity.','One master reference recording plus its exact transcript defines this character\'s identity on iPhone.');
      });
      if(!document.getElementById('iosCloneReferenceText')){
        const field=document.createElement('div');
        field.className='field';
        field.innerHTML=`<label>Reference recording transcript</label><textarea id="iosCloneReferenceText" rows="3" placeholder="Type exactly what is spoken in the reference recording.">${esc(c.cloneReferenceText||'')}</textarea><div class="mini">ZipVoice requires the transcript to match the reference audio. This stays with the character identity.</div>`;
        const fileInput=document.getElementById('luxRefFile');
        const anchor=fileInput?.closest('.field')||body.lastElementChild;
        if(anchor)anchor.insertAdjacentElement('afterend',field);else body.appendChild(field);
        document.getElementById('iosCloneReferenceText').onchange=e=>{
          c.cloneReferenceText=e.target.value.trim();
          save();
        };
      }
    }

    // Parler Voice Designer is still a desktop model. Keep the controls visible so
    // character descriptions remain portable, but do not pretend it can run locally.
    const designer=document.getElementById('voiceDesignerPanel');
    if(designer){
      const s=document.getElementById('vdStatus');
      if(s)s.textContent='desktop designer';
      const btn=document.getElementById('generateDesignedVoices');
      if(btn){
        btn.disabled=true;
        btn.textContent='Voice Designer · Desktop';
      }
      const progress=document.getElementById('vdProgress');
      if(progress)progress.textContent='Parler Voice Designer stays on desktop for now. Designed/cloned voices can still be used on iPhone through the native ZipVoice clone engine.';
    }

    const title=document.querySelector('#voiceModal h2');
    if(title&&!title.textContent.includes('iPhone'))title.textContent+=` · iPhone`;
  }

  const previousOpenVoiceLab=window.openVoiceLab;
  if(typeof previousOpenVoiceLab==='function'){
    window.openVoiceLab=function(id){
      previousOpenVoiceLab(id);
      patchVoiceLab(id);
    };
  }

  function enhanceIOS(){
    document.title=`Ashen Voice Studio iPhone v${VERSION}`;
    const v=document.querySelector('.version');if(v)v.textContent=`v${VERSION} iPhone`;
    const chip=document.querySelector('.nativeProjectPanel .chip');if(chip)chip.textContent=`iPhone Native v${VERSION}`;
    const banner=document.getElementById('memoryBanner');
    if(banner){
      banner.classList.remove('hidden');
      banner.textContent='iPhone native inference: KittenTTS + Piper run fully on-device. Character clones use ZipVoice on-device. No Ragnarok connection is required for these engines.';
    }
    document.querySelectorAll('.nativeEngineChip').forEach(el=>{
      if(el.textContent.trim()==='LuxTTS')el.textContent='ZipVoice Clone';
    });
    document.querySelectorAll('.recipe').forEach(el=>{
      if(el.textContent.includes('LuxTTS'))el.textContent=el.textContent.replaceAll('LuxTTS','ZipVoice Clone');
    });
    const ep=document.getElementById('engineProgress');
    if(ep&&/KittenTTS \/ Piper \/ LuxTTS|Local engines not checked/i.test(ep.textContent)){
      ep.textContent='iPhone local engines ready to check · KittenTTS / Piper / ZipVoice';
    }
  }

  const previousRender=window.render;
  if(typeof previousRender==='function'){
    window.render=function(){previousRender();enhanceIOS()};
  }

  // Boot already ran before this last overlay file is evaluated in some builds.
  queueMicrotask(enhanceIOS);
  window.AshenIOS.version=VERSION;
})();
