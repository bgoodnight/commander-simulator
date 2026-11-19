(() => {
 const original=window.fetch.bind(window);
 window.fetch=async(input,options)=>{
  const u=new URL(typeof input==="string"?input:(input instanceof URL?input.href:input.url),location.href);
  if(u.hostname==="gorge-r2-direct-api-preview.darbosama.workers.dev" && u.pathname.startsWith("/v1/ui/")){
   if(u.pathname!=="/v1/ui/batch")return new Response("{}",{status:404});
   const deck=u.searchParams.get("deck");
   if(!["magnus_v1_7","mortarion_v2_3"].includes(deck))return new Response("{}",{status:404});
   const batch=await (await original(`./${deck}-preliminary.json`)).json();
   return new Response(JSON.stringify({schema:"gorge-r2-original-ui-batch-response-v1",population:"preliminary_decisive_only",deck,status:"ready",batch}),{status:200,headers:{"Content-Type":"application/json"}});
  }
  return original(input,options);
 };
})();
