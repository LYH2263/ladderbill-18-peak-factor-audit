<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON, formatTime } from '../api'

const s = ref({})
const factor = ref(null)
const audits = ref({ items: [], total: 0, page: 1, page_size: 10 })
const newValue = ref(null)
const operator = ref('admin')
const note = ref('')
const error = ref('')
const saving = ref(false)

const loadFactor = async () => { factor.value = await getJSON('/api/settings/peak-factor') }
const loadAudits = async (page = 1) => {
  audits.value = await getJSON(`/api/settings/peak-factor/audits?page=${page}&page_size=${audits.value.page_size}`)
}

const save = async () => {
  error.value = ''
  if (newValue.value == null) { error.value = '请输入新系数'; return }
  saving.value = true
  try {
    await putJSON('/api/settings/peak-factor', {
      new_value: Number(newValue.value),
      operator: operator.value || 'admin',
      note: note.value || null,
    })
    newValue.value = null
    note.value = ''
    await Promise.all([loadFactor(), loadAudits(1), loadSettings()])
  } catch (e) {
    let msg = e.message
    try { msg = JSON.parse(e.message).detail || msg } catch {}
    error.value = msg
  } finally {
    saving.value = false
  }
}

const loadSettings = async () => { s.value = await getJSON('/api/settings') }
const goPage = async (p) => {
  if (p < 1 || p > totalPages.value) return
  await loadAudits(p)
}
const totalPages = () => Math.max(1, Math.ceil(audits.value.total / audits.value.page_size))

onMounted(async () => {
  await Promise.all([loadSettings(), loadFactor(), loadAudits(1)])
})
</script>
<template>
  <div class="page">
    <h1>参数</h1>
    <ul class="panel kv">
      <li v-for="(v, k) in s" :key="k"><span class="muted">{{ k }}</span> {{ v }}</li>
    </ul>

    <div class="panel">
      <h2 class="block-title">尖峰系数 peak_factor</h2>
      <p v-if="factor" class="muted">
        当前生效值 <strong>{{ factor.peak_factor }}</strong>
        · 更新时间 {{ formatTime(factor.coefficient_as_of) }}
      </p>
      <div class="factor-form">
        <label>新系数 <input type="number" v-model.number="newValue" min="0.01" step="0.01" /></label>
        <label>操作者 <input type="text" v-model="operator" maxlength="64" /></label>
        <label class="note">备注 <input type="text" v-model="note" maxlength="200" placeholder="可选" /></label>
        <button :disabled="saving" @click="save">保存并记审计</button>
      </div>
      <p v-if="error" class="err">⚠ {{ error }}</p>
    </div>

    <div class="panel">
      <h2 class="block-title">变更审计</h2>
      <table>
        <thead><tr><th>#</th><th>旧值</th><th>新值</th><th>操作者</th><th>备注</th><th>操作时间</th></tr></thead>
        <tbody>
          <tr v-for="a in audits.items" :key="a.id">
            <td>{{ a.id }}</td>
            <td>{{ a.old_value }}</td>
            <td>{{ a.new_value }}</td>
            <td>{{ a.operator }}</td>
            <td>{{ a.note ?? '—' }}</td>
            <td class="muted">{{ formatTime(a.changed_at) }}</td>
          </tr>
          <tr v-if="!audits.items.length"><td colspan="6" class="muted">暂无变更记录</td></tr>
        </tbody>
      </table>
      <div class="pager">
        <button :disabled="audits.page <= 1" @click="goPage(audits.page - 1)">上一页</button>
        <span class="muted">第 {{ audits.page }} / {{ totalPages() }} 页 · 共 {{ audits.total }} 条</span>
        <button :disabled="audits.page >= totalPages()" @click="goPage(audits.page + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>
<style scoped>
.kv { list-style: none; padding: 1rem; margin: 0; }
.kv li { padding: 0.35rem 0; border-bottom: 1px solid color-mix(in srgb, var(--muted) 25%, transparent); }
.block-title { margin: 0 0 0.6rem; font-size: 1.05rem; }
.factor-form { display: flex; flex-wrap: wrap; gap: 1rem; align-items: end; }
.factor-form input { width: 8rem; margin-left: 0.35rem; }
.factor-form .note input { width: 14rem; }
.err { color: #ff9c8a; margin: 0.6rem 0 0; }
.pager { display: flex; gap: 0.75rem; align-items: center; margin-top: 0.8rem; }
.pager button:disabled { opacity: 0.45; cursor: default; }
</style>
