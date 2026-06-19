const axios = require('axios');
const admin = require('firebase-admin');

// গিটহাব সিক্রেট থেকে টোকেন রিড করা
const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);

if (!admin.apps.length) {
    admin.initializeApp({
        credential: admin.credential.cert(serviceAccount)
    });
}

const db = admin.firestore(); // Firestore Database ব্যবহার করা হচ্ছে

// ✅ হেল্পার ফাংশন: যেকোনো ফরম্যাটের তারিখকে YYYY-MM-DD-এ রূপান্তর
function convertToYYYYMMDD(dateStr) {
    if (!dateStr) return null;

    // যদি ইতিমধ্যে YYYY-MM-DD ফরম্যাটে থাকে
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return dateStr;
    }

    // DD-MM-YYYY ফরম্যাট চেক
    const parts = dateStr.split('-');
    if (parts.length === 3) {
        // ধরে নিচ্ছি ফরম্যাট DD-MM-YYYY
        const day = parts[0].padStart(2, '0');
        const month = parts[1].padStart(2, '0');
        const year = parts[2];
        // যাচাই করা যে দিন, মাস, বছর বৈধ
        if (day >= 1 && day <= 31 && month >= 1 && month <= 12 && year.length === 4) {
            return `${year}-${month}-${day}`;
        }
        // যদি DD-MM-YY (ছোট বছর) হয়, তাহলে 20 যোগ করুন
        if (year.length === 2) {
            const fullYear = `20${year}`;
            return `${fullYear}-${month}-${day}`;
        }
    }

    // যদি DD/MM/YYYY ফরম্যাটে থাকে
    if (dateStr.includes('/')) {
        const parts = dateStr.split('/');
        if (parts.length === 3) {
            const day = parts[0].padStart(2, '0');
            const month = parts[1].padStart(2, '0');
            const year = parts[2];
            if (year.length === 4) return `${year}-${month}-${day}`;
        }
    }

    // ফরম্যাট না বুঝলে আসল স্ট্রিং ফেরত দিন (পরে এরর দেখাবে)
    console.warn('⚠️ অজানা ফরম্যাট:', dateStr);
    return dateStr;
}

async function updateFirebase() {
    try {
        // আপনার সচল ভার্সেল এপিআই লিংক
        const apiUrl = "https://dsex-scraper-final-to-main-app.vercel.app/api";
        const { data } = await axios.get(apiUrl);

        if (data && data.success) {
            const batch = db.batch();
            
            data.data.forEach(item => {
                // ✅ তারিখকে YYYY-MM-DD ফরম্যাটে রূপান্তর
                const originalDate = item.date;
                const formattedDate = convertToYYYYMMDD(originalDate);
                
                if (!formattedDate) {
                    console.warn(`⚠️ তারিখ রূপান্তর ব্যর্থ: ${originalDate}, আইটেম স্কিপ করা হচ্ছে`);
                    return;
                }

                // তারিখটিকে ডকুমেন্ট আইডি বানাচ্ছি যাতে ডুপ্লিকেট না হয়
                const docRef = db.collection('dse_market_data').doc(formattedDate);
                batch.set(docRef, {
                    date: formattedDate, // ✅ ফরম্যাট করা তারিখ সংরক্ষণ
                    dsex_index: item.dsex_index,
                    updatedAt: admin.firestore.FieldValue.serverTimestamp()
                });
            });

            await batch.commit();
            console.log("✅ Firebase Firestore সফলভাবে আপডেট হয়েছে!");
        } else {
            console.log("❌ API সফল হয়নি।");
        }
    } catch (error) {
        console.error("❌ Firebase আপডেট করতে সমস্যা:", error);
        process.exit(1);
    }
}

updateFirebase();
