// ── 全局 View 切换 ──
function switchGlobalView(idx) {
  document.querySelectorAll('.gnav-tab').forEach((t, i) => t.classList.toggle('on', i === idx));
  document.querySelectorAll('.gnav-view-section').forEach((v, i) => v.classList.toggle('gnav-active', i === idx));
}

// ── 前台 Tab 切换 ──
function switchTab(el, prefix, tab) {
  el.parentElement.querySelectorAll('.p-tab').forEach(t => t.classList.remove('act'));
  el.classList.add('act');
  ['ongoing','upcoming','ended'].forEach(t => {
    var content = document.getElementById(prefix + '-' + t);
    if (content) content.style.display = (t === tab) ? 'block' : 'none';
  });
}

// ── 页面跳转 ──
function goPage(name) {
  document.querySelectorAll('.p-page').forEach(p => p.classList.remove('show'));
  var target = document.getElementById('page-' + name);
  if (target) target.classList.add('show');
  closeDropdown();
}

// ── 下拉菜单 ──
function toggleDropdown(e) {
  e.stopPropagation();
  document.getElementById('acDropdown').classList.toggle('show');
}
function closeDropdown() {
  var dd = document.getElementById('acDropdown');
  if (dd) dd.classList.remove('show');
}
document.addEventListener('click', closeDropdown);

// ── 抽屉 ──
function openDrawer() {
  document.getElementById('drawerOverlay').classList.add('show');
  document.getElementById('drawerPanel').classList.add('show');
}
function closeDrawer() {
  document.getElementById('drawerOverlay').classList.remove('show');
  document.getElementById('drawerPanel').classList.remove('show');
}

// ── Chip 胶囊切换 ──
function switchChip(el, prefix, tab) {
  el.parentElement.querySelectorAll('.cz-chip').forEach(c => c.classList.remove('on'));
  el.classList.add('on');
  ['ongoing','upcoming','ended'].forEach(t => {
    var content = document.getElementById(prefix + '-' + t);
    if (content) content.style.display = (t === tab) ? 'block' : 'none';
  });
}

// ── 设备切换（Web/App） ──
function switchDevice(webId, appId, devBtns, idx) {
  devBtns.forEach((b, i) => {
    b.style.background = i === idx ? '#2D81FF' : 'transparent';
    b.style.color = i === idx ? '#EAECEF' : '#5E6673';
  });
  document.getElementById(webId).style.display = idx === 0 ? 'block' : 'none';
  document.getElementById(appId).style.display = idx === 1 ? 'block' : 'none';
}

// ── 后台页面切换 ──
function swPage(el, idx) {
  document.querySelectorAll('.sb-item').forEach(s => s.classList.remove('on'));
  el.classList.add('on');
  document.querySelectorAll('.page').forEach((p, i) => {
    p.classList.toggle('hide', i !== idx);
  });
}

// ── 弹窗 ──
document.querySelectorAll('.modal-bg').forEach(m => {
  m.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('show'); });
});

// ═══════════════════════════════════════════════════════════════════════
// [TEMPLATE] 数据驱动 CRUD 模式（后台管理必用）
// 核心原则：JS 数组存数据 → render 渲染列表 → 弹窗按索引读写
// ═══════════════════════════════════════════════════════════════════════

/*
// ── Step 1：数据源（JS 数组） ──
var items = [
  { name: '项目A', status: '已上线', type: '类型1', sort: 1 },
  { name: '项目B', status: '未上线', type: '类型2', sort: 2 },
];
var currentIdx = -1;  // -1=新增, >=0=编辑

// ── Step 2：渲染函数（列表 + 统计全部从数组生成） ──
function renderList() {
  var container = document.getElementById('listContainer');
  var html = '';
  items.forEach(function(item, i) {
    html += '<tr>'
      + '<td><b>' + item.name + '</b></td>'
      + '<td>' + item.status + '</td>'
      + '<td>' + item.type + '</td>'
      + '<td>'
      +   '<span onclick="openEdit(' + i + ')" style="cursor:pointer;color:#2D81FF;">编辑</span> '
      +   '<span onclick="deleteItem(' + i + ')" style="cursor:pointer;color:#F53F3F;">删除</span>'
      + '</td>'
      + '</tr>';
  });
  container.innerHTML = html;
  // 统计实时更新
  document.getElementById('itemCount').textContent = '共 ' + items.length + ' 条';
}

// ── Step 3：新增（空表单 + 默认值） ──
function openAdd() {
  currentIdx = -1;
  document.getElementById('f-name').value = '';
  document.getElementById('f-type').value = '类型1';  // 默认值
  document.getElementById('editModal').style.display = 'flex';
}

// ── Step 4：编辑（按索引读数据填入弹窗） ──
function openEdit(idx) {
  currentIdx = idx;
  var d = items[idx];
  document.getElementById('f-name').value = d.name;
  document.getElementById('f-type').value = d.type;
  document.getElementById('editModal').style.display = 'flex';
}

// ── Step 5：保存 = 写数据 + render + 关弹窗（三步缺一不可） ──
function saveItem() {
  var name = document.getElementById('f-name').value.trim();
  if (!name) { alert('请填写名称'); return; }
  var type = document.getElementById('f-type').value;

  if (currentIdx >= 0) {
    // 编辑：写回原数组
    items[currentIdx].name = name;
    items[currentIdx].type = type;
  } else {
    // 新增：push 到数组
    items.push({ name: name, status: '未上线', type: type, sort: items.length + 1 });
  }

  renderList();                                                    // 刷新列表
  document.getElementById('editModal').style.display = 'none';     // 关弹窗
}

// ── Step 6：删除（二次确认 + splice + render） ──
function deleteItem(idx) {
  if (!confirm('确定删除「' + items[idx].name + '」？')) return;
  items.splice(idx, 1);
  renderList();
}

// ── 初始渲染 ──
renderList();
*/
