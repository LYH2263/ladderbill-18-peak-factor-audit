<script setup>
import { ref } from 'vue'
import { postJSON, formatTime } from '../api'
import TierLadder from '../components/TierLadder.vue'
import SegmentTable from '../components/SegmentTable.vue'
const kwh = ref(220)
const peak = ref(false)
const result = ref(null)
const run = async () => {
  result.value = await postJSON('/api/bill', { kwh: kwh.value, peak: peak.value, persist: true })
}
</script>
<template>
  <div class="page work">
    <h1>测算工作台</h1>
    <div class="panel form-row">
      <label>电量(kWh) <input type="number" v-model.number="kwh" min="0" step="1" /></label>
      <label><input type="checkbox" v-model="peak" /> 尖峰系数</label>
      <button @click="run">计算并入库</button>
    </div>
    <div v-if="result" class="panel">
      <p>
        合计 ¥{{ result.total }} <span class="muted">记录#{{ result.run_id }}</span>
      </p>
      <p class="muted coeff">
        当前尖峰系数 <strong>{{ result.coefficient }}</strong>
        <template v-if="peak">（本次已按尖峰计）</template>
        <template v-else>（本次按平段 ×1.0 计）</template>
        · 系数更新时间 {{ formatTime(result.coefficient_as_of) }}
      </p>
      <TierLadder :segments="result.segments" />
      <SegmentTable :rows="result.segments" />
    </div>
  </div>
</template>
<style scoped>
.form-row { display: flex; flex-wrap: wrap; gap: 1rem; align-items: end; }
input[type=number] { width: 6rem; margin-left: 0.35rem; }
.coeff { margin-top: -0.4rem; }
</style>
