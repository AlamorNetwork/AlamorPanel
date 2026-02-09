function toggleSecurityFields() {
    const sec = document.getElementById('security').value;
    const realitySect = document.getElementById('reality-sect');
    sec === 'reality' ? realitySect.classList.remove('hidden') : realitySect.classList.add('hidden');
}

async function saveInbound() {
    const payload = {
        base: {
            enabled: document.getElementById('enabled').checked,
            remark: document.getElementById('remark').value,
            protocol: document.getElementById('protocol').value,
            port: parseInt(document.getElementById('port').value),
            listen: document.getElementById('listen').value
        },
        auth: {
            uuid: document.getElementById('uuid').value,
            decryption: document.getElementById('decryption').value
        },
        // سایر فیلدها به همین ترتیب با QuerySelector جمع‌آوری می‌شوند
    };

    console.log("Deploying Configuration...", payload);
    
    const response = await fetch('/api/cores/add-inbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const res = await response.json();
    alert("Response from Server: " + res.status);
}