// Staging-only invitation widgets. Not loaded by the production Deck Lab.
// Request form requires a configured Cloudflare Turnstile widget whose response
// is supplied by getTurnstileToken; never submit a request without verification.
export function mountInvitationRequest(root, { endpoint, getTurnstileToken }) {
  if(!root || !endpoint || typeof getTurnstileToken!=="function")
    throw new Error("Invitation intake configuration required");
  root.replaceChildren();
  const form=document.createElement("form");
  const email=document.createElement("input");
  email.type="email";email.required=true;email.maxLength=254;email.placeholder="Your email";
  email.autocomplete="email";
  const name=document.createElement("input");
  name.type="text";name.maxLength=80;name.placeholder="Name (optional)";
  const note=document.createElement("textarea");
  note.maxLength=500;note.placeholder="How do you know the group? (optional)";
  const submit=document.createElement("button");
  submit.type="submit";submit.textContent="Request invitation";
  const status=document.createElement("p");status.setAttribute("role","status");
  form.append(email,name,note,submit,status);
  form.addEventListener("submit",async event=>{
    event.preventDefault();submit.disabled=true;status.textContent="";
    try {
      const token=await getTurnstileToken();
      if(!token)throw new Error("Complete verification first.");
      const response=await fetch(endpoint,{
        method:"POST",headers:{"content-type":"application/json"},
        body:JSON.stringify({email:email.value,display_name:name.value,
          note:note.value,turnstile_token:token})
      });
      if(!response.ok)throw new Error("Request unavailable. Try again later.");
      status.textContent="Request received. An invitation is not automatic.";
      form.reset();
    }catch(e){status.textContent=e.message||"Request unavailable.";}
    finally{submit.disabled=false;}
  });
  root.append(form);
}
export async function mountInvitationAdmin(root,{apiBase="",fetchImpl=fetch}={}){
  if(!root)throw new Error("Admin root required");
  const fetchJson=async(path,options={})=>{
    const r=await fetchImpl(apiBase+path,{credentials:"include",...options});
    if(!r.ok)throw new Error("Invitation admin API error: "+r.status);
    return r.json();
  };
  async function render(){
    const {requests}=await fetchJson("/v1/admin/invitations");
    root.replaceChildren();
    const list=document.createElement("ul");
    for(const request of requests){
      const item=document.createElement("li");
      const summary=document.createElement("span");
      summary.textContent=request.email+" · "+request.status;
      item.append(summary);
      if(request.status==="pending"){
        for(const [text,status] of [
          ["Approve for invitation","awaiting_access_allowlist"],
          ["Decline","declined"]
        ]){
          const button=document.createElement("button");
          button.type="button";button.textContent=text;
          button.addEventListener("click",async()=>{
            button.disabled=true;
            try{
              await fetchJson("/v1/admin/invitations/"+encodeURIComponent(request.id)+"/review",{
                method:"POST",headers:{"content-type":"application/json"},
                body:JSON.stringify({status})
              });
              await render();
            }catch(e){button.disabled=false;summary.textContent=e.message;}
          });
          item.append(button);
        }
      }
      list.append(item);
    }
    root.append(list);
    const info=document.createElement("p");
    info.textContent="Approved requests still require adding the email to the Cloudflare Access allowlist manually.";
    root.append(info);
  }
  await render();
}
