// Ashen Voice Studio native Kokoro worker v1.3.1
// Native Tauri fix: keep the Kokoro runtime, voice embeddings, and ONNX WASM backend local.
let tts=null;
let currentDevice=null;
let currentDtype=null;
let inferenceTail=Promise.resolve();
const STYLE_DIM=256;
const SAMPLE_RATE=24000;
const LOCAL_VOICE_DATA_URL='/vendor/kokoro-js/voices';
const REMOTE_VOICE_DATA_URL='https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/voices';
const voiceCache=new Map();
const blendCache=new Map();

function ensureReadableStreamAsyncIterator(){const RS=self.ReadableStream;if(!RS||!self.Symbol||!Symbol.asyncIterator)return;if(!RS.prototype[Symbol.asyncIterator]){Object.defineProperty(RS.prototype,Symbol.asyncIterator,{configurable:true,writable:true,value:async function*(){const reader=this.getReader();try{while(true){const r=await reader.read();if(r.done)return;yield r.value}}finally{try{reader.releaseLock()}catch{}}}})}if(!RS.prototype.values){Object.defineProperty(RS.prototype,'values',{configurable:true,writable:true,value:function(){return this[Symbol.asyncIterator]()}})}}
function status(message,busy=true){postMessage({type:'status',message,busy})}
function errorText(e){return(e&&e.stack)||String(e&&e.message||e)}

async function configureModule(mod){
  // kokoro-js exposes env.wasmPaths specifically so host apps can prevent
  // Transformers.js / ONNX Runtime from dynamically importing its backend from jsDelivr.
  // That remote dynamic import is unreliable inside Tauri/WebKitGTK.
  const wasmUrl=new URL('/vendor/ort/ort-wasm-simd-threaded.jsep.wasm',self.location.origin).href;
  try{
    if(mod?.env){
      mod.env.wasmPaths={wasm:wasmUrl};
    }
  }catch(e){console.warn('Could not override Kokoro wasmPaths',e)}

  // Use packaged voice embeddings when this kokoro-js build exposes the setter.
  try{
    if(typeof mod?.setVoiceDataUrl==='function'){
      mod.setVoiceDataUrl(new URL(LOCAL_VOICE_DATA_URL+'/',self.location.origin).href.replace(/\/$/,''));
    }
  }catch(e){console.warn('Could not set local Kokoro voice path',e)}
  return mod;
}

async function getModule(){
  ensureReadableStreamAsyncIterator();
  status('Loading bundled Kokoro runtime…',true);
  try{
    const mod=await import('/vendor/kokoro-js/dist/kokoro.web.js');
    return configureModule(mod);
  }catch(localErr){
    console.warn('Bundled kokoro-js import failed, trying CDN',localErr);
    status('Bundled runtime unavailable · trying browser fallback…',true);
    const mod=await import('https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/dist/kokoro.web.js');
    return configureModule(mod);
  }
}

async function tryEngine(KokoroTTS,model,attempt,progress_callback){
  status(`Loading Kokoro model · ${attempt.device} ${attempt.dtype}`,true);
  const engine=await KokoroTTS.from_pretrained(model,{device:attempt.device,dtype:attempt.dtype,progress_callback});
  tts=engine;currentDevice=attempt.device;currentDtype=attempt.dtype;
  return attempt;
}

async function loadEngine(model,device,dtype){
  if(tts&&device===currentDevice&&dtype===currentDtype)return{device,dtype};
  try{await tts?.dispose?.()}catch{}
  tts=null;
  const mod=await getModule();
  const{KokoroTTS}=mod;
  if(!KokoroTTS)throw new Error('KokoroTTS export missing from bundled runtime');
  const progress_callback=data=>{try{postMessage({type:'progress',data})}catch{}};
  const attempts=[];
  const add=(d,t)=>{if(!attempts.some(a=>a.device===d&&a.dtype===t))attempts.push({device:d,dtype:t})};

  // On Linux Tauri/WebKitGTK, WASM is the dependable backend. If the UI asks for
  // auto/webgpu we can try it, but always fall back to local WASM q8 then q4.
  add(device,dtype);
  add('wasm','q8');
  add('wasm','q4');

  let lastErr=null;
  for(const attempt of attempts){
    try{return await tryEngine(KokoroTTS,model,attempt,progress_callback)}
    catch(e){
      lastErr=e;
      console.warn('Kokoro load attempt failed',attempt,e);
      status(`${attempt.device} ${attempt.dtype} failed · trying fallback…`,true);
      try{await tts?.dispose?.()}catch{}
      tts=null;
    }
  }
  throw lastErr||new Error('No Kokoro runtime configuration could be loaded');
}

async function fetchVoiceData(id){
  const local=`${LOCAL_VOICE_DATA_URL}/${encodeURIComponent(id)}.bin`;
  try{
    const r=await fetch(local,{cache:'force-cache'});
    if(r.ok)return new Float32Array(await r.arrayBuffer());
  }catch{}
  const remote=`${REMOTE_VOICE_DATA_URL}/${encodeURIComponent(id)}.bin`;
  const r=await fetch(remote,{cache:'force-cache'});
  if(!r.ok)throw new Error(`Could not load voice ${id}: HTTP ${r.status}`);
  return new Float32Array(await r.arrayBuffer());
}
async function getVoiceData(id){
  if(voiceCache.has(id))return voiceCache.get(id);
  const data=await fetchVoiceData(id);
  if(data.length<STYLE_DIM)throw new Error(`Voice ${id} returned invalid style data`);
  voiceCache.set(id,data);
  return data;
}
async function getBlendData(a,b,w){
  const weight=Math.max(0,Math.min(1,Number(w)));
  if(a===b||weight>=.9999)return getVoiceData(a);
  if(weight<=.0001)return getVoiceData(b);
  const key=`${a}|${b}|${weight.toFixed(4)}`;
  if(blendCache.has(key))return blendCache.get(key);
  const[A,B]=await Promise.all([getVoiceData(a),getVoiceData(b)]);
  if(A.length!==B.length)throw new Error('Voice embedding sizes do not match');
  const out=new Float32Array(A.length),bw=1-weight;
  for(let i=0;i<out.length;i++)out[i]=A[i]*weight+B[i]*bw;
  blendCache.set(key,out);
  return out;
}
function pcmResult(a){
  const src=a?.audio||a?.samples||a?.data;
  if(!src)throw new Error('Kokoro returned no PCM audio');
  const pcm=src instanceof Float32Array?new Float32Array(src):new Float32Array(src);
  return{pcm,sampleRate:a?.sampling_rate||a?.sampleRate||SAMPLE_RATE};
}
async function generatePreset(text,voice,speed){
  const a=await tts.generate(text,{voice,speed:speed||1});
  return pcmResult(a);
}
async function generateBlend(text,voiceA,voiceB,weight,speed){
  if(!tts)throw new Error('Voice engine is not loaded');
  if(!voiceA||!voiceB)throw new Error('Blend requires two voices');
  if(voiceA===voiceB)return generatePreset(text,voiceA,speed);
  const blended=await getBlendData(voiceA,voiceB,weight);
  const original=tts.generate_from_ids;
  tts.generate_from_ids=async function(input_ids,{speed:innerSpeed=1}={}){
    const dims=input_ids?.dims||[];
    const n=dims.length?dims[dims.length-1]:0;
    const numTokens=Math.min(Math.max(n-2,0),509);
    const offset=numTokens*STYLE_DIM;
    const styleData=blended.slice(offset,offset+STYLE_DIM);
    if(styleData.length!==STYLE_DIM)throw new Error('Blend style slice was incomplete');
    const TensorCtor=input_ids.constructor;
    const inputs={input_ids,style:new TensorCtor('float32',styleData,[1,STYLE_DIM]),speed:new TensorCtor('float32',[innerSpeed],[1])};
    const{waveform}=await tts.model(inputs);
    return{audio:new Float32Array(waveform.data),sampling_rate:SAMPLE_RATE};
  };
  try{return pcmResult(await tts.generate(text,{voice:voiceA,speed:speed||1}))}
  finally{tts.generate_from_ids=original}
}
function enqueue(fn){const run=inferenceTail.then(fn,fn);inferenceTail=run.catch(()=>{});return run}
function postPcm(id,r,extra={}){const pcm=r.pcm instanceof Float32Array?r.pcm:new Float32Array(r.pcm);postMessage({id,ok:true,pcmBuffer:pcm.buffer,sampleRate:r.sampleRate||SAMPLE_RATE,...extra},[pcm.buffer])}

self.onmessage=async ev=>{
  const m=ev.data||{},id=m.id;
  try{
    if(m.type==='ping'){postMessage({id,ok:true,type:'pong',version:'1.3.1'});return}
    if(m.type==='load'){const r=await loadEngine(m.model,m.device,m.dtype);status(`Voice engine ready · ${r.device} ${r.dtype}`,false);postMessage({id,ok:true,...r});return}
    if(m.type==='generate'){
      if(!tts)throw new Error('Voice engine is not loaded');
      status('Generating voice preview…',true);
      const r=await enqueue(()=>generatePreset(m.text,m.voice,m.speed||1));
      status('Voice preview generated',false);postPcm(id,r);return
    }
    if(m.type==='generateBlend'){
      if(!tts)throw new Error('Voice engine is not loaded');
      status(`Blending ${m.voiceA} + ${m.voiceB} in voice space…`,true);
      const r=await enqueue(()=>generateBlend(m.text,m.voiceA,m.voiceB,m.weight,m.speed||1));
      status('Blended voice generated',false);postPcm(id,r,{blend:true});return
    }
    if(m.type==='dispose'){try{await tts?.dispose?.()}catch{}tts=null;currentDevice=null;currentDtype=null;voiceCache.clear();blendCache.clear();postMessage({id,ok:true});return}
    throw new Error('Unknown worker command');
  }catch(e){postMessage({id,ok:false,error:errorText(e)})}
};
