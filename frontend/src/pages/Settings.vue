<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'

const s = ref({})
const value = ref(null)
const operator = ref('admin')
const remark = ref('')
const error = ref('')
const saved = ref(null)
const audits = ref({ items: [], total: 0, page: 1, page_size: 10 })

const pages = computed(() => Math.max(1, Math.ceil(audits.value.total / audits.value.page_size)))

const loadSettings = async () => {
  s.value = await getJSON('/api/settings')
  value.value = Number(s.value.peak_factor)
}
const loadAudits = async (page = 1) => {
  audits.value = await getJSON(`/api/settings/peak_factor/audits?page=${page}&page_size=${audits.value.page_size}`)
}
const save = async () => {
  error.value = ''
  saved.value = null
  try {
    const r = await putJSON('/api/settings/peak_factor', {
      value: Number(value.value),
      operator: operator.value,
      remark: remark.value || null,
    })
    saved.value = r.audit
    remark.value = ''
    await loadSettings()
    await loadAudits(1) // 回到第一页，最新条目立即置顶可见
  } catch (e) {
    let msg = e.message
    try { msg = JSON.parse(e.message).detail ?? e.message } catch { /* 保留原文 */ }
    error.value = typeof msg === 'string' ? msg : JSON.stringify(msg)
  }
}

onMounted(async () => { await loadSettings(); await loadAudits(1) })
</script>
<template>
  <div class="page">
    <h1>参数</h1>
    <ul class="panel kv">
      <li v-for="(v, k) in s" :key="k"><span class="muted">{{ k }}</span> {{ v }}</li>
    </ul>

    <div class="panel">
      <h2>修改尖峰系数</h2>
      <div class="form-row">
        <label>新系数值 <input type="number" v-model.number="value" min="0" step="0.01" /></label>
        <label>操作者 <input type="text" v-model="operator" /></label>
        <label>备注(可选) <input type="text" v-model="remark" placeholder="变更原因" /></label>
        <button @click="save">保存</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="saved" class="ok">
        已生效：{{ saved.old_value }} → {{ saved.new_value }}（{{ saved.operator }} · {{ saved.changed_at }}）
      </p>
    </div>

    <div class="panel">
      <h2>系数变更审计</h2>
      <table>
        <thead><tr><th>#</th><th>旧值</th><th>新值</th><th>操作者</th><th>备注</th><th>时间</th></tr></thead>
        <tbody>
          <tr v-for="a in audits.items" :key="a.id" :class="{ latest: saved && a.id === saved.id }">
            <td>{{ a.id }}</td>
            <td>{{ a.old_value }}</td>
            <td>{{ a.new_value }}</td>
            <td>{{ a.operator }}</td>
            <td>{{ a.remark ?? '—' }}</td>
            <td class="muted">{{ a.changed_at }}</td>
          </tr>
          <tr v-if="!audits.items.length"><td colspan="6" class="muted">暂无变更记录</td></tr>
        </tbody>
      </table>
      <div class="pager">
        <button :disabled="audits.page <= 1" @click="loadAudits(audits.page - 1)">上一页</button>
        <span class="muted">第 {{ audits.page }} / {{ pages }} 页 · 共 {{ audits.total }} 条</span>
        <button :disabled="audits.page >= pages" @click="loadAudits(audits.page + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>
<style scoped>
.kv { list-style: none; padding: 1rem; margin: 0; }
.kv li { padding: 0.35rem 0; border-bottom: 1px solid color-mix(in srgb, var(--muted) 25%, transparent); }
h2 { font-size: 1rem; margin: 0 0 0.75rem; }
.form-row { display: flex; flex-wrap: wrap; gap: 1rem; align-items: end; }
.form-row input { margin-left: 0.35rem; }
.form-row input[type=number] { width: 6rem; }
.error { color: #ff7a7a; margin: 0.75rem 0 0; }
.ok { color: var(--accent); margin: 0.75rem 0 0; }
.latest td { background: color-mix(in srgb, var(--accent) 12%, transparent); }
.pager { display: flex; gap: 0.75rem; align-items: center; margin-top: 0.75rem; }
.pager button:disabled { opacity: 0.4; cursor: default; }
</style>
