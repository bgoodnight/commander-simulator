// Separate PUBLIC intake Worker, never routed through the protected deck API.
// Disabled by default. Requires Turnstile secret and isolated D1 binding.
// Never accept a user's "approved" role, create accounts or grant Access.
import { submitInvitation,validateRequest } from "../community-access/invitations.mjs";
import { ApiError } from "../community-access/store.mjs";
const response=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{
 "content-type":"application/json; charset=utf-8","cache-control":"no-store",
 "x-content-type-options":"nosniff","access-control-allow-origin":"null"
}});
export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.pathname!=="/request-invitation" || request.method!=="POST")
      return response({error:"not_found"},404);
    if(env.ENABLE_INVITATION_INTAKE!=="true" || !env.REQUEST_DB || !env.TURNSTILE_SECRET_KEY)
      return response({error:"requests_disabled"},503);
    if(!env.REQUEST_FORM_ORIGIN || request.headers.get("origin")!==env.REQUEST_FORM_ORIGIN)
      return response({error:"origin_forbidden"},403);
    if(!request.headers.get("content-type")?.startsWith("application/json"))
      return response({error:"invalid_content_type"},415);
    const raw=await request.text();
    if(new TextEncoder().encode(raw).length>5000)return response({error:"request_too_large"},413);
    let payload;
    try{payload=JSON.parse(raw);}catch{return response({error:"invalid_json"},400);}
    const token=payload?.turnstile_token;
    if(typeof token!=="string"||token.length<8||token.length>2048)return response({error:"captcha_required"},400);
    try {
      const form=new FormData();
      form.set("secret",env.TURNSTILE_SECRET_KEY);
      form.set("response",token);
      const verification=await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify",{
        method:"POST",body:form
      });
      if(!verification.ok)return response({error:"verification_unavailable"},503);
      const verdict=await verification.json();
      if(!verdict.success || verdict.hostname!==env.REQUEST_FORM_HOSTNAME)
        return response({error:"captcha_failed"},403);
      const {email,display_name,note}=validateRequest(payload);
      return response(await submitInvitation(env.REQUEST_DB,{email,display_name,note}),202);
    }catch(e){
      if(e instanceof ApiError)return response({error:e.code},e.status);
      return response({error:"request_unavailable"},503);
    }
  }
};
