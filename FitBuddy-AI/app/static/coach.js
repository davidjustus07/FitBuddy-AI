const $ = s => document.querySelector(s);
async function api(url){const r=await fetch(url);const d=await r.json();if(!r.ok)throw new Error(d.detail||'Request failed');return d}
function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
async function load(){
  try{
    const [summary,users,feedback]=await Promise.all([api('/api/coach/summary'),api('/api/users'),api('/api/feedback?limit=20')]);
    $('#stats').innerHTML=[['Users',summary.users],['Plans',summary.plans],['Feedback',summary.feedback],['Avg rating',summary.average_rating??'—']].map(([a,b])=>`<div class="stat"><strong>${esc(b)}</strong><span>${a}</span></div>`).join('');
    $('#users').innerHTML=users.length?`<div class="table-like">${users.map(u=>`<div class="row"><span><strong>${esc(u.name)}</strong><br><span class="muted">${esc(u.goal.replaceAll('_',' '))} · ${esc(u.experience)}</span></span><span>${u.days_per_week} days/wk<br><span class="muted">${u.session_minutes} min</span></span></div>`).join('')}</div>`:'<p class="muted">No users yet.</p>';
    $('#feedback').innerHTML=feedback.length?feedback.map(f=>`<div class="feedback-item"><strong>${esc(f.user_name)} · ${f.rating}/5</strong><p>${esc(f.difficulty.replaceAll('_',' '))} · energy ${esc(f.energy)}</p><p>${esc(f.comments||'No comment')}</p></div>`).join(''):'<p class="muted">No feedback yet.</p>';
  }catch(e){$('#users').innerHTML=`<p class="muted">${esc(e.message)}</p>`}
}
document.addEventListener('DOMContentLoaded',()=>{$('#reload').addEventListener('click',load);load()});
