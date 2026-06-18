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

async function updateFirebase() {
    try {
        // আপনার সচল ভার্সেল এপিআই লিংক
        const apiUrl = "https://dsex-scraper-final-to-main-app.vercel.app/api";
        const { data } = await axios.get(apiUrl);

        if (data && data.success) {
            const batch = db.batch();
            
            data.data.forEach(item => {
                // তারিখটিকে ডকুমেন্ট আইডি বানাচ্ছি যাতে ডুপ্লিকেট না হয়
                const docRef = db.collection('dse_market_data').doc(item.date);
                batch.set(docRef, {
                    date: item.date,
                    dsex_index: item.dsex_index,
                    updatedAt: admin.firestore.FieldValue.serverTimestamp()
                });
            });

            await batch.commit();
            console.log("Firebase Firestore successfully updated!");
        } else {
            console.log("API response was not successful.");
        }
    } catch (error) {
        console.error("Error updating Firebase:", error);
        process.exit(1);
    }
}

updateFirebase();
