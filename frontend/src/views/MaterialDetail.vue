<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import type { Material, Page } from '../types'
import { formatQuantity, formatSignedQuantity } from '../utils/format'
interface Movement {id:number;movement_no:string;operation_type:string;quantity_delta:string;before_quantity:string;after_quantity:string;reason:string;created_at:string}
const route=useRoute();const router=useRouter();const auth=useAuthStore();const material=ref<Material|null>(null);const movements=ref<Movement[]>([]);const deleting=ref(false)
onMounted(async()=>{material.value=(await api.get<Material>(`/materials/${route.params.id}`)).data;movements.value=(await api.get<Page<Movement>>('/stock-movements',{params:{material_id:route.params.id,page_size:50}})).data.items})
async function removeMaterial(){
  if(!material.value||deleting.value)return
  const row=material.value
  const label=row.mpn||row.name
  if(Number(row.quantity)!==0||Number(row.reserved_quantity)!==0){
    ElMessage.warning(`“${label}”仍有库存或预留，请先完成出库或取消预留并清零后再删除`)
    return
  }
  try{
    await ElMessageBox.confirm(
      `确认删除“${label}”？删除后将从物料列表移除，历史库存流水仍会保留。`,
      '删除物料',
      {type:'warning',confirmButtonText:'删除',cancelButtonText:'取消'},
    )
  }catch{
    return
  }
  deleting.value=true
  try{
    await api.delete(`/materials/${row.id}`)
    ElMessage.success(`“${label}”已删除`)
    await router.push('/materials')
  }catch{
    // 具体错误由统一请求拦截器显示。
  }finally{
    deleting.value=false
  }
}
</script>
<template><div v-if="material" class="page"><div class="page-header"><div><div class="code">{{material.code}}</div><h1 class="page-title">{{material.name}}</h1><div class="page-subtitle">{{material.manufacturer}} · {{material.mpn||'暂无 MPN'}} · {{material.package||'未设置封装'}}</div></div><div><el-button v-if="auth.can('material:manage')" type="danger" plain :loading="deleting" @click="removeMaterial">删除物料</el-button><el-button v-if="auth.can('material:manage')" @click="$router.push(`/materials/${material.id}/edit`)">编辑资料</el-button><el-button type="primary" @click="$router.push({path:'/inventory',query:{material_id:material.id}})">库存操作</el-button></div></div><section class="stock"><div><span>当前库存</span><b>{{formatQuantity(material.quantity)}}</b><small>{{material.unit}}</small></div><div><span>项目预留</span><b>{{formatQuantity(material.reserved_quantity)}}</b><small>{{material.unit}}</small></div><div><span>可用库存</span><b :class="Number(material.available_quantity)<=Number(material.safety_stock)?'danger-number':'success-number'">{{formatQuantity(material.available_quantity)}}</b><small>{{material.unit}}</small></div><div><span>安全库存</span><b>{{formatQuantity(material.safety_stock)}}</b><small>{{material.unit}}</small></div></section><el-card class="card"><el-tabs><el-tab-pane label="技术资料"><el-descriptions :column="3" border><el-descriptions-item label="规格值">{{material.specification||'—'}}</el-descriptions-item><el-descriptions-item label="封装">{{material.package||'—'}}</el-descriptions-item><el-descriptions-item label="Footprint">{{material.footprint||'—'}}</el-descriptions-item><el-descriptions-item label="单价">¥ {{material.unit_price}}</el-descriptions-item><el-descriptions-item label="RoHS">{{material.rohs_status}}</el-descriptions-item><el-descriptions-item label="生命周期">{{material.lifecycle_status}}</el-descriptions-item><el-descriptions-item label="条形码">{{material.barcode||'—'}}</el-descriptions-item><el-descriptions-item label="数据手册"><a v-if="material.datasheet_url" :href="material.datasheet_url" target="_blank">打开链接</a><span v-else>—</span></el-descriptions-item><el-descriptions-item label="标签"><el-tag v-for="tag in material.tags" :key="tag" size="small">{{tag}}</el-tag></el-descriptions-item><el-descriptions-item label="备注" :span="3">{{material.notes||'—'}}</el-descriptions-item></el-descriptions></el-tab-pane><el-tab-pane label="库存流水"><el-table :data="movements"><el-table-column prop="movement_no" label="流水号" width="200"/><el-table-column prop="operation_type" label="类型" width="130"/><el-table-column label="变化" width="100"><template #default="{row}">{{formatSignedQuantity(row.quantity_delta)}}</template></el-table-column><el-table-column label="操作前"><template #default="{row}">{{formatQuantity(row.before_quantity)}}</template></el-table-column><el-table-column label="操作后"><template #default="{row}">{{formatQuantity(row.after_quantity)}}</template></el-table-column><el-table-column prop="reason" label="原因" min-width="180"/><el-table-column prop="created_at" label="时间" width="180"/></el-table></el-tab-pane><el-tab-pane label="附件与替代料"><el-empty description="附件管理功能将在此区域提供"/></el-tab-pane></el-tabs></el-card></div><div v-else class="page"><el-skeleton :rows="8" animated/></div></template>
<style scoped>.code{font-size:12px;color:#3478c5;font-weight:700;letter-spacing:1px;margin-bottom:5px}.stock{display:grid;grid-template-columns:repeat(4,1fr);background:#112c52;color:white;border-radius:14px;padding:24px;margin-bottom:16px}.stock div{padding:0 24px;border-right:1px solid #ffffff20}.stock div:last-child{border:0}.stock span{display:block;color:#9fb6d3;font-size:13px}.stock b{font-size:30px;display:inline-block;margin-top:8px}.stock small{margin-left:6px;color:#9fb6d3}@media(max-width:700px){.stock{grid-template-columns:1fr 1fr;gap:20px}.stock div{border:0;padding:0}}</style>
