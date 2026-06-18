const axios = require('axios');
const cheerio = require('cheerio');

module.exports = async (req, res) => {
    // CORS অন করা যাতে যেকোনো ওয়েবসাইট বা অ্যাপ থেকে এই API কল করা যায়
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');

    try {
        const url = "https://www.dsebd.org/recent_market_information.php";
        const { data } = await axios.get(url, {
            headers: { 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' 
            }
        });
        
        const $ = cheerio.load(data);
        const marketData = [];

        // DSE টেবিল স্ক্র্যাপ করার লজিক
        $('table.table-bordered.background-white.text-center tr').each((index, element) => {
            const cols = $(element).find('td');
            if (cols.length >= 7) {
                const date = $(cols[0]).text().trim();
                const dsexIndex = $(cols[5]).text().trim(); // ৬ষ্ঠ কলাম (Index 5)

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
