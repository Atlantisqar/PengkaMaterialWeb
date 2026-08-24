<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Box,
  Connection,
  DataAnalysis,
  Document,
  Fold,
  Goods,
  Location,
  Menu,
  Operation,
  Setting,
  ShoppingCart,
  Tickets,
  User,
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const mobile = ref(false)
const navigation = [
  ['/dashboard', '仪表盘', DataAnalysis, 'dashboard:view'],
  ['/locations', '库位管理', Location, 'location:manage'],
  ['/cables', '线缆管理', Connection, 'material:view'],
  ['/categories', '分类管理', Box, 'category:manage'],
  ['/materials', '物料管理', Goods, 'material:view'],
  ['/inventory', '库存操作', Operation, 'inventory:operate'],
  ['/movements', '库存流水', Tickets, 'inventory:view'],
  ['/projects', '项目与 BOM', Document, 'project:manage'],
  ['/stocktakes', '盘点管理', Operation, 'inventory:view'],
  ['/suppliers', '供应商', ShoppingCart, 'supplier:manage'],
  ['/purchases', '采购管理', ShoppingCart, 'purchase:manage'],
  ['/users', '用户与角色', User, ['user:manage', 'role:manage']],
  ['/audit', '审计日志', Tickets, 'audit:view'],
  ['/settings', '系统设置', Setting, 'role:manage'],
] as const
const visibleNavigation = computed(() => navigation.filter((item) => auth.can(item[3])))
function closeMobileNavigation() {
  mobile.value = false
}
function handleNavigationClick(path: string) {
  closeMobileNavigation()
  if (path === '/locations' && route.path === '/locations') {
    window.dispatchEvent(new Event('locations:show-overview'))
  }
}
function isNavigationActive(path: string) {
  return route.path === path || route.path.startsWith(`${path}/`)
}
async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="shell">
    <el-aside
      :width="collapsed ? '72px' : '238px'"
      class="sidebar"
      :class="{ 'mobile-open': mobile }"
    >
      <div class="brand">
        <div class="brand-mark">P</div>
        <div v-if="!collapsed" class="brand-copy"><b>嘭咔智能</b><span>Material OS</span></div>
      </div>
      <nav class="nav-scroll" aria-label="主导航" data-testid="sidebar-navigation">
        <router-link
          v-for="item in visibleNavigation"
          :key="item[0]"
          :to="item[0]"
          class="nav-item"
          :class="{ active: isNavigationActive(item[0]) }"
          :title="collapsed ? item[1] : undefined"
          :data-nav-path="item[0]"
          @click="handleNavigationClick(item[0])"
        >
          <el-icon><component :is="item[2]" /></el-icon>
          <span v-if="!collapsed" class="nav-label">{{ item[1] }}</span>
        </router-link>
      </nav>
      <button class="collapse desktop-only" @click="collapsed = !collapsed">
        <el-icon><Fold /></el-icon><span v-if="!collapsed">收起导航</span>
      </button>
    </el-aside>
    <el-container>
      <el-header class="topbar"
        ><el-button text class="mobile-trigger" @click="mobile = !mobile"
          ><el-icon><Menu /></el-icon
        ></el-button>
        <div>
          <b>{{ route.meta.title }}</b
          ><span class="crumb"> / 统一库存中心</span>
        </div>
        <el-dropdown
          ><div class="user">
            <el-avatar :size="32">{{ auth.user?.full_name.slice(0, 1) }}</el-avatar>
            <div class="desktop-only">
              <b>{{ auth.user?.full_name }}</b
              ><span>{{ auth.user?.role.name }}</span>
            </div>
          </div>
          <template #dropdown
            ><el-dropdown-menu
              ><el-dropdown-item disabled>{{ auth.user?.username }}</el-dropdown-item
              ><el-dropdown-item divided @click="logout"
                >安全退出</el-dropdown-item
              ></el-dropdown-menu
            ></template
          ></el-dropdown
        ></el-header
      >
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.shell {
  min-height: 100vh;
}
.sidebar {
  position: fixed;
  z-index: 20;
  height: 100vh;
  background: #10264a;
  color: white;
  transition: width 0.2s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  isolation: isolate;
}
.brand {
  height: 72px;
  flex: 0 0 72px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
}
.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #58b4ff, #3971e5);
  font-weight: 900;
  font-size: 22px;
  box-shadow: 0 8px 20px #07172e;
}
.brand-copy {
  display: flex;
  flex-direction: column;
  white-space: nowrap;
}
.brand-copy span {
  font-size: 11px;
  letter-spacing: 1.5px;
  color: #86a6d2;
  margin-top: 2px;
}
.nav-scroll {
  position: relative;
  z-index: 1;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
  scrollbar-gutter: stable;
  overscroll-behavior: contain;
}
.nav-scroll::-webkit-scrollbar {
  width: 5px;
}
.nav-scroll::-webkit-scrollbar-thumb {
  background: #ffffff26;
  border-radius: 10px;
}
.nav-item {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  height: 48px;
  margin-bottom: 4px;
  padding: 0 16px;
  gap: 14px;
  border-radius: 9px;
  color: #aec1df;
  cursor: pointer;
  white-space: nowrap;
  transition:
    color 0.15s,
    background 0.15s;
}
.nav-item .el-icon {
  flex: 0 0 auto;
  font-size: 17px;
}
.nav-item:hover,
.nav-item.active {
  color: white;
  background: #214577;
}
.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}
.collapse {
  position: relative;
  z-index: 2;
  flex: 0 0 52px;
  width: calc(100% - 16px);
  margin: 0 8px 8px;
  padding: 0 10px;
  border: 0;
  border-top: 1px solid #ffffff16;
  background: #10264a;
  color: #90a9cc;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.sidebar[style*='72px'] .nav-item {
  justify-content: center;
  padding: 0;
  gap: 0;
}
.sidebar[style*='72px'] .collapse {
  justify-content: center;
}
.sidebar + .el-container {
  margin-left: 238px;
  transition: margin-left 0.2s;
}
.sidebar[style*='72px'] + .el-container {
  margin-left: 72px;
}
.topbar {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid #e8edf4;
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
}
.crumb {
  font-weight: 400;
  color: #8a99ac;
}
.user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.user div {
  display: flex;
  flex-direction: column;
  font-size: 13px;
}
.user span {
  color: #8492a6;
  font-size: 11px;
}
.main {
  padding: 0;
  background: #f3f6fb;
}
.mobile-trigger {
  display: none;
}
@media (max-width: 760px) {
  .sidebar {
    transform: translateX(-100%);
    width: 238px !important;
  }
  .sidebar.mobile-open {
    transform: translateX(0);
  }
  .sidebar + .el-container {
    margin-left: 0;
  }
  .mobile-trigger {
    display: inline-flex;
  }
  .crumb {
    display: none;
  }
}
</style>
