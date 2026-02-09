function toggleSecurityUI(val) {
    const realityFields = document.getElementById('realityFields');
    val === 'reality' ? realityFields.classList.remove('d-none') : realityFields.classList.add('d-none');
}

async function submitXray() {
    const form = document.getElementById('xrayForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // اضافه کردن چک‌باکس‌ها که FormData به صورت پیش‌فرض نمی‌گیرد
    data.tcp_tfo = form.querySelector('[name="tcp_tfo"]').checked;

    // بستن مودال و نمایش لودینگ (مانند AlamorHub)
    const modal = bootstrap.Modal.getInstance(document.getElementById('xrayModal'));
    modal.hide();
    
    // فراخوانی فانکشن نصب که قبلا در AlamorHub داشتی
    startInstall('xray', 'xrayForm'); 
}