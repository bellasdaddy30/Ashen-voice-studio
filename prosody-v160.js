/* Ashen Voice Studio phrase prosody v1.6.0
   Chatterbox phrase-level rendering with stable character identity.
   The manuscript segmentation remains authoritative. This layer only subdivides
   an existing production line for performance, then joins the resulting audio.
*/
(function(){
  'use strict';

  const PROSODY_VERSION='1.6.0';
  const TAURI=()=>window.__TAURI__?.core?.invoke;
  const EMOTION_RAMP={
    neutral:0.04, solemn:0.08, tense:0.16, urgent:0.22, fearful:0.20,
    grief:0.10, angry:0.30, intimate:0.06, deadpan:0.02, ominous:0.18, whispered:0.05
  };

  function invokeNative(command,args={}) {
    const invoke=TAURI();
    if(!invoke) throw new Error('Native Tauri voice bridge is unavailable.');
    return invoke(command,args);
  }

  function clamp(v,a,b){return Math.max(a,Math.min(b,v));}

  // Split only inside an already-correct production segment. Sentence endings
  // are strongest boundaries; clause punctuation is used when a sentence is long.
  function splitPerformancePhrases(text){
    text=String(text||'').replace(/\s+/g,' ').trim();
    if(!text)return [];
    const sentences=text.match(/[^.!?]+(?:[.!?]+|$)/g)||[text];
    const out=[];
    for(const raw of sentences){
      let s=raw.trim();
      if(!s)continue;
      if(s.length<=135){out.push(s);continue;}
      const parts=s.split(/(?<=[,;:])\s+|\s+(?=[—–-])|(?<=\s)\u2014(?=\s)/g).map(x=>x.trim()).filter(Boolean);
      let buf='';
      for(const part of parts){
        if(!buf){buf=part;continue;}
        if((buf+' '+part).length<=105){buf+=' '+part;}
        else{out.push(buf);buf=part;}
      }
      if(buf)out.push(buf);
    }
    return out.length?out:[text];
  }

  function phrasePauses(phrases,emotion,delivery){
    const last=phrases.length-1;
    return phrases.map((p,i)=>{
      const end=/[!?]$/.test(p);
      const comma=/[,;:]$/.test(p);
      let pause=end?.46:(comma?.26:.12);
      if(i===last)pause=.18;
      const e=String(emotion||'neutral');
      const d=String(delivery||'natural');
      if(e==='angry'||e==='urgent')pause*=.82;
      if(e==='solemn'||e==='grief'||e==='ominous')pause*=1.22;
      if(d==='controlled')pause*=1.10;
      if(d==='clipped')pause*=.72;
      if(d==='hesitant')pause*=1.32;
      if(d==='soft')pause*=1.18;
      return clamp(pause,0,.9);
    });
  }

  function readWav(blob){
    return blob.arrayBuffer().then(buf=>{
      const v=new DataView(buf);
      if(v.getUint32(0,false)!==0x52494646||v.getUint32(8,false)!==0x57415645)throw new Error('Generated audio was not a RIFF/WAV file.');
      let off=12,fmt=null,data=null;
      while(off+8<=v.byteLength){
        const id=v.getUint32(off,false),len=v.getUint32(off+4,true); off+=8;
        if(id===0x666d7420){
          fmt={format:v.getUint16(off,true),channels:v.getUint16(off+2,true),rate:v.getUint32(off+4,true),bits:v.getUint16(off+14,true)};
        }else if(id===0x64617461){data={off,len};break;}
        off+=len+(len&1);
      }
      if(!fmt||!data||fmt.format!==1||fmt.channels!==1||fmt.bits!==16)throw new Error('Only mono PCM16 WAV output is supported by the prosody joiner.');
      const samples=new Float32Array(data.len/2);
      for(let i=0;i<samples.length;i++)samples[i]=v.getInt16(data.off+i*2,true)/32768;
      return {samples,rate:fmt.rate};
    });
  }

  function encodeWav(samples,rate){
    const out=new ArrayBuffer(44+samples.length*2),v=new DataView(out);
    const put=(o,s)=>{for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};
    put(0,'RIFF');v.setUint32(4,36+samples.length*2,true);put(8,'WAVE');put(12,'fmt ');
    v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,rate,true);
    v.setUint32(28,rate*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);put(36,'data');v.setUint32(40,samples.length*2,true);
    for(let i=0;i<samples.length;i++)v.setInt16(44+i*2,Math.round(clamp(samples[i],-1,1)*32767),true);
    return new Blob([out],{type:'audio/wav'});
  }

  function joinPcm(parts,rate,pauses,crossfadeMs=12){
    const xfade=Math.max(0,Math.floor(rate*crossfadeMs/1000));
    let total=0;
    for(let i=0;i<parts.length;i++)total+=parts[i].samples.length+(i<parts.length-1?Math.floor(rate*pauses[i]):0);
    total-=Math.max(0,(parts.length-1)*xfade);
    const out=new Float32Array(Math.max(0,total));
    let pos=0;
    for(let n=0;n<parts.length;n++){
      const src=parts[n].samples;
      if(n===0){out.set(src,pos);pos+=src.length;}
      else{
        const overlap=Math.min(xfade,src.length,pos);
        const start=pos-overlap;
        for(let j=0;j<overlap;j++){
          const a=j/overlap;
          out[start+j]=out[start+j]*(1-a)+src[j]*a;
        }
        out.set(src.subarray(overlap),pos);
        pos+=src.length-overlap;
      }
      if(n<parts.length-1){
        const silence=Math.floor(rate*pauses[n]);
        pos+=silence;
      }
    }
    return encodeWav(out,rate);
  }

  async function renderChatterboxPhrase(text,c,emotion,intensity,delivery,seed){
    const ref=typeof dbGet==='function'?await dbGet('native-voice-ref:'+c.id).catch(()=>null):null;
    const payload={
      op:'synthesize',engine:'chatterbox',text:applyDictionary(text),
      model:'ResembleAI/Chatterbox',voice:c.engineVoice||'',
      speed:Number(c.speed||1),emotion,emotion_intensity:intensity,delivery,
      character_id:c.id,lux_steps:4,seed
    };
    if(ref){
      const bytes=new Uint8Array(await ref.arrayBuffer());
      let binary='';
      for(let i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode(...bytes.subarray(i,i+0x8000));
      payload.reference_audio_b64=btoa(binary);
      payload.reference_name=ref.name||'reference.wav';
    }
    const r=await invokeNative('native_tts',{request:payload});
    if(!r?.ok||!r.wav_b64)throw new Error(r?.error||'Chatterbox returned no audio.');
    const bin=atob(r.wav_b64),bytes=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
    return new Blob([bytes],{type:'audio/wav'});
  }

  async function synthesizeChatterboxProsody(text,c){
    const phrases=splitPerformancePhrases(text);
    const emotion=c.emotion||'neutral',delivery=c.delivery||'natural';
    const base=clamp(Number(c.emotionIntensity??.7),0,1);
    const ramp=EMOTION_RAMP[emotion]??.08;
    const seedBase=Number(c.prosodySeed||((String(c.id||'').length*7919)%100000));
    const blobs=[];
    for(let i=0;i<phrases.length;i++){
      const t=phrases.length===1?1:i/(phrases.length-1);
      // Emotional contour: intensity changes gradually across the line while the
      // speaker reference never changes. Dramatic emotions build toward the tail.
      const intensity=clamp(base-ramp*.45+ramp*t,0,1);
      const seed=seedBase+i*997;
      blobs.push(await renderChatterboxPhrase(phrases[i],c,emotion,intensity,delivery,seed));
    }
    const pcm=[];
    for(const b of blobs)pcm.push(await readWav(b));
    const rate=pcm[0]?.rate||24000;
    if(pcm.some(x=>x.rate!==rate))throw new Error('Chatterbox phrase sample rates did not match.');
    return joinPcm(pcm,rate,phrasePauses(phrases,emotion,delivery),12);
  }

  const original=window.synthesizeProfile;
  if(typeof original==='function'){
    window.synthesizeProfile=async function(text,c){
      c=c||{};
      if(String(c.engine||'').toLowerCase()!=='chatterbox')return original(text,c);
      return synthesizeChatterboxProsody(text,c);
    };
  }

  window.AshenProsody={
    version:PROSODY_VERSION,
    split:splitPerformancePhrases,
    synthesize:synthesizeChatterboxProsody
  };
})();
