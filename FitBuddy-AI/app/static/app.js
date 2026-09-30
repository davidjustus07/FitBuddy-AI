const state = { user: null, plan: null };
const $ = (s) => document.querySelector(s);

async function api(url, options={}) {
  const res = await fetch(url, { headers: {'Content-Type':'application/json', ...(options.headers||{})}, ...options });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

function formToPayload(form) {
  const fd = new FormData(form);
  return {
    name: fd.get('name'), age: Number(fd.get('age')), goal: fd.get('goal'), experience: fd.get('experience'),
    days_per_week: Number(fd.get('days_per_week')), session_minutes: Number(fd.get('session_minutes')),
    equipment: String(fd.get('equipment') || '').split(',').map(x=>x.trim()).filter(Boolean),
    diet: fd.get('diet'), limitations: fd.get('limitations') || '', preferences: fd.get('preferences') || ''
  };
}

function renderPlan(plan) {
  const root = $('#planView');
  $('#planEmpty').hidden = true; root.hidden = false;
  root.innerHTML = '';
  const p = plan.plan;
  const summary = document.createElement('div'); summary.className='plan-summary';
  summary.innerHTML = `<h3>${escapeHtml(p.title || 'FitBuddy Plan')}</h3><p>${escapeHtml(p.summary || '')}</p><p class="muted">Version ${plan.version} · ${escapeHtml(plan.source)}</p>`;
  root.appendChild(summary);
  if (p.adjustment) { const note=document.createElement('div'); note.className='plan-summary'; note.innerHTML=`<strong>Latest adjustment</strong><p>${escapeHtml(p.adjustment)}</p>`; root.appendChild(note); }
  (p.sessions || []).forEach(s => {
    const el=document.createElement('div'); el.className='session';
    el.innerHTML=`<div class="session-title"><strong>${escapeHtml(s.day)} · ${escapeHtml(s.focus || '')}</strong><span class="pill">${escapeHtml(String(s.duration_minutes))} min · ${escapeHtml(s.intensity || '')}</span></div>`;
    (s.exercises || []).forEach(e=>{const x=document.createElement('div');x.className='exercise';x.innerHTML=`<span>${escapeHtml(e.name)}</span><span>${escapeHtml(String(e.sets))} sets · ${escapeHtml(String(e.reps))}</span>`;el.appendChild(x)});
    root.appendChild(el);
  });
  if ((p.rest_days||[]).length) { const r=document.createElement('div');r.className='plan-summary';r.innerHTML=`<strong>Rest / recovery days</strong><p>${p.rest_days.map(escapeHtml).join(' · ')}</p>`;root.appendChild(r); }
  if (p.nutrition) { const n=document.createElement('div');n.className='plan-summary';n.innerHTML=`<strong>Nutrition guidance</strong><ul class="mini-list">${(p.nutrition.principles||[]).map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ul>`;root.appendChild(n); }
  if (p.safety_note) { const s=document.createElement('p');s.className='status';s.textContent=p.safety_note;root.appendChild(s); }
  $('#feedbackSection').hidden = false;
}

function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

async function loadHealth() {
  try { const h=await api('/health'); $('#modeBadge').textContent=h.demo_mode ? 'Demo mode' : (h.gemini_configured ? 'Gemini AI' : 'Fallback mode'); }
  catch { $('#modeBadge').textContent='Offline'; }
}

async function saveProfile(e) {
  e.preventDefault(); $('#profileStatus').textContent='Saving profile and generating your plan…';
  try {
    state.user=await api('/api/users',{method:'POST',body:JSON.stringify(formToPayload(e.target))});
    state.plan=await api(`/api/users/${state.user.id}/plans/generate`,{method:'POST'});
    renderPlan(state.plan); $('#profileStatus').textContent='Plan generated successfully.';
  } catch(err) { $('#profileStatus').textContent=err.message; }
}

async function generateAgain() {
  if(!state.user){ $('#profileStatus').textContent='Save your profile first.'; return; }
  $('#refreshPlan').disabled=true; $('#profileStatus').textContent='Generating an updated plan…';
  try { state.plan=await api(`/api/users/${state.user.id}/plans/generate`,{method:'POST'}); renderPlan(state.plan); $('#profileStatus').textContent='Updated plan generated.'; }
  catch(err){ $('#profileStatus').textContent=err.message; } finally { $('#refreshPlan').disabled=false; }
}

async function submitFeedback(e) {
  e.preventDefault(); if(!state.user || !state.plan) return;
  const fd=new FormData(e.target);
  const payload={plan_id:state.plan.id,rating:Number(fd.get('rating')),energy:fd.get('energy'),difficulty:fd.get('difficulty'),comments:fd.get('comments')||''};
  $('#feedbackStatus').textContent='Saving feedback…';
  try { await api(`/api/users/${state.user.id}/feedback`,{method:'POST',body:JSON.stringify(payload)}); $('#feedbackStatus').textContent='Saved. Click “Generate again” to apply the feedback to the next plan.'; e.target.reset(); }
  catch(err){ $('#feedbackStatus').textContent=err.message; }
}

document.addEventListener('DOMContentLoaded',()=>{
  loadHealth();
  $('#profileForm').addEventListener('submit',saveProfile);
  $('#refreshPlan').addEventListener('click',generateAgain);
  $('#feedbackForm').addEventListener('submit',submitFeedback);
});
