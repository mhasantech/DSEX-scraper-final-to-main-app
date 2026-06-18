const axios = require('axios');
const cheerio = require('cheerio');
const https = require('https');

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');

    try {
        const url = "https://www.dsebd.org/recent_market_information.php";
        
        // SSL সার্টিফিকেট ভেরিফিকেশন ইগনোর করার জন্য এজেন্ট তৈরি
        const httpsAgent = new https.Agent({  
            rejectUnauthorized: false 
        });

        const { data } = await axios.get(url, {
            headers: { 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' 
            },
            httpsAgent: httpsAgent // এজেন্টটি এখানে যুক্ত করা হলো
        });
        
        const $ = cheerio.load(data);
        const marketData = [];

        $('table.table-bordered.background-white.text-center tr').each((index, element) => {
            const cols = $(element).find('td');
            if (cols.length >= 7) {
                const date = $(cols[0]).text().trim();
                const dsexIndex = $(cols[5]).text().trim();

                if (date.toLowerCase() !== 'date' && date !== "") {
                    marketData.push({
                        date: date,
                        dsex_index: dsexIndex
                    });
                }
            }
        });

        res.status(200).json({ success: true, total: marketData.length, data: marketData });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
};
