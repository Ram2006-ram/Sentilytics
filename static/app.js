// ============================================================
// SENTILYTICS
// YouTube AI Sentiment Analysis
// Frontend JavaScript
// ============================================================


// ============================================================
// BACKEND URL
// ============================================================

const API_BASE_URL = "http://127.0.0.1:5000";


// ============================================================
// GLOBAL DATA
// ============================================================

let allComments = [];

let sentimentChartInstance = null;
let trendChartInstance = null;


// ============================================================
// DOM ELEMENTS
// ============================================================

const videoUrl =
    document.getElementById("videoUrl");

const analyzeBtn =
    document.getElementById("analyzeBtn");

const statusMessage =
    document.getElementById("statusMessage");


// ============================================================
// CHECK BACKEND
// ============================================================

async function checkBackend() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/health`,
                {
                    method: "GET"
                }
            );


        const data =
            await response.json();


        console.log(
            "Backend health response:",
            data
        );


        if (
            response.ok &&
            data.success !== false
        ) {

            console.log(
                "Sentilytics backend is online."
            );


            showMessage(
                "Backend online — Ready to analyze.",
                "success"
            );

        } else {

            showMessage(
                "Backend is running but returned an error.",
                "error"
            );
        }


    } catch (error) {

        console.error(
            "Backend connection error:",
            error
        );


        showMessage(
            "Backend offline. Please start Flask.",
            "error"
        );
    }
}


// ============================================================
// EXTRACT YOUTUBE VIDEO ID
// ============================================================

function extractVideoId(url) {

    if (!url) {

        return "";
    }


    url =
        url.trim();


    // --------------------------------------------------------
    // Direct 11-character YouTube video ID
    // --------------------------------------------------------

    if (
        /^[A-Za-z0-9_-]{11}$/.test(url)
    ) {

        return url;
    }


    // --------------------------------------------------------
    // Try URL object first
    // --------------------------------------------------------

    try {

        let normalizedUrl =
            url;


        if (
            !/^https?:\/\//i.test(
                normalizedUrl
            )
        ) {

            normalizedUrl =
                "https://" +
                normalizedUrl;
        }


        const parsedUrl =
            new URL(
                normalizedUrl
            );


        const hostname =
            parsedUrl.hostname
                .toLowerCase()
                .replace(
                    /^www\./,
                    ""
                );


        // ----------------------------------------------------
        // youtube.com/watch?v=VIDEO_ID
        // ----------------------------------------------------

        if (
            hostname === "youtube.com" ||
            hostname === "m.youtube.com"
        ) {

            const v =
                parsedUrl.searchParams.get(
                    "v"
                );


            if (
                v &&
                /^[A-Za-z0-9_-]{11}$/.test(v)
            ) {

                return v;
            }


            // ------------------------------------------------
            // /shorts/VIDEO_ID
            // ------------------------------------------------

            const shortsMatch =
                parsedUrl.pathname.match(
                    /^\/shorts\/([A-Za-z0-9_-]{11})/
                );


            if (shortsMatch) {

                return shortsMatch[1];
            }


            // ------------------------------------------------
            // /embed/VIDEO_ID
            // ------------------------------------------------

            const embedMatch =
                parsedUrl.pathname.match(
                    /^\/embed\/([A-Za-z0-9_-]{11})/
                );


            if (embedMatch) {

                return embedMatch[1];
            }
        }


        // ----------------------------------------------------
        // youtu.be/VIDEO_ID
        // ----------------------------------------------------

        if (
            hostname === "youtu.be"
        ) {

            const id =
                parsedUrl.pathname
                    .replace(
                        /^\/+/,
                        ""
                    )
                    .split("/")[0];


            if (
                /^[A-Za-z0-9_-]{11}$/.test(id)
            ) {

                return id;
            }
        }


    } catch (error) {

        console.log(
            "URL parser fallback:",
            error
        );
    }


    // --------------------------------------------------------
    // Regex fallback
    // --------------------------------------------------------

    const patterns = [

        /youtube\.com\/watch\?v=([A-Za-z0-9_-]{11})/i,

        /youtube\.com\/watch\?.*v=([A-Za-z0-9_-]{11})/i,

        /youtu\.be\/([A-Za-z0-9_-]{11})/i,

        /youtube\.com\/shorts\/([A-Za-z0-9_-]{11})/i,

        /youtube\.com\/embed\/([A-Za-z0-9_-]{11})/i,

        /youtube-nocookie\.com\/embed\/([A-Za-z0-9_-]{11})/i

    ];


    for (
        const pattern of patterns
    ) {

        const match =
            url.match(
                pattern
            );


        if (match) {

            return match[1];
        }
    }


    return "";
}


// ============================================================
// SHOW STATUS MESSAGE
// ============================================================

function showMessage(
    text,
    type = "normal"
) {

    if (!statusMessage) {

        return;
    }


    statusMessage.textContent =
        text;


    if (
        type === "success"
    ) {

        statusMessage.style.color =
            "#15803d";

    } else if (
        type === "error"
    ) {

        statusMessage.style.color =
            "#b42318";

    } else {

        statusMessage.style.color =
            "";
    }
}


// ============================================================
// ANALYZE VIDEO
// ============================================================

async function analyzeVideo() {

    console.log(
        "Analyze button clicked."
    );


    // --------------------------------------------------------
    // Check input element
    // --------------------------------------------------------

    if (!videoUrl) {

        console.error(
            "ERROR: #videoUrl element not found."
        );


        showMessage(
            "Input field error. Please check index.html.",
            "error"
        );


        return;
    }


    const url =
        videoUrl.value.trim();


    // --------------------------------------------------------
    // Check empty URL
    // --------------------------------------------------------

    if (!url) {

        showMessage(
            "Please paste a YouTube URL.",
            "error"
        );


        return;
    }


    // --------------------------------------------------------
    // Extract video ID
    // --------------------------------------------------------

    const videoId =
        extractVideoId(
            url
        );


    console.log(
        "Extracted Video ID:",
        videoId
    );


    // --------------------------------------------------------
    // Validate video ID
    // --------------------------------------------------------

    if (!videoId) {

        showMessage(
            "Invalid YouTube URL. Please paste a valid YouTube video or Shorts URL.",
            "error"
        );


        return;
    }


    // --------------------------------------------------------
    // Disable button
    // --------------------------------------------------------

    if (analyzeBtn) {

        analyzeBtn.disabled =
            true;


        analyzeBtn.innerHTML =
            "<span>Analyzing...</span><b>⏳</b>";
    }


    showMessage(
        "Connecting to Sentilytics backend...",
        "normal"
    );


    try {

        // ====================================================
        // BUILD API URL
        // ====================================================

        const apiUrl =
            `${API_BASE_URL}/api/analyze?video_id=${encodeURIComponent(videoId)}`;


        console.log(
            "Calling backend:",
            apiUrl
        );


        // ====================================================
        // CALL FLASK BACKEND
        // ====================================================

        const response =
            await fetch(
                apiUrl,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        // ====================================================
        // READ RESPONSE
        // ====================================================

        let data;


        try {

            data =
                await response.json();

        } catch (jsonError) {

            console.error(
                "JSON parsing error:",
                jsonError
            );


            throw new Error(
                "Backend returned an invalid response."
            );
        }


        console.log(
            "Backend response:",
            data
        );


        // ====================================================
        // BACKEND ERROR
        // ====================================================

        if (!response.ok) {

            throw new Error(
                data.error ||
                `Backend error: ${response.status}`
            );
        }


        // ====================================================
        // ACCEPT SUCCESS RESPONSE
        // ====================================================

        if (
            data.success === false
        ) {

            throw new Error(
                data.error ||
                "Video analysis failed."
            );
        }


        // ====================================================
        // CHECK COMMENTS
        // ====================================================

        allComments =
            Array.isArray(
                data.comments
            )
                ? data.comments
                : [];


        // ====================================================
        // UPDATE VIDEO INFORMATION
        // ====================================================

        updateVideoInfo(
            data.video
        );


        // ====================================================
        // UPDATE STATISTICS
        // ====================================================

        updateStatistics(
            data
        );


        // ====================================================
        // DISPLAY COMMENTS
        // ====================================================

        renderComments(
            allComments
        );


        // ====================================================
        // UPDATE CHARTS
        // ====================================================

        updateCharts(
            data
        );


        // ====================================================
        // SUCCESS MESSAGE
        // ====================================================

        showMessage(
            `Analysis completed successfully! ${allComments.length} comments analyzed.`,
            "success"
        );


        // ====================================================
        // SCROLL TO RESULTS
        // ====================================================

        const statsSection =
            document.querySelector(
                ".stats-section"
            );


        if (statsSection) {

            setTimeout(
                function () {

                    statsSection.scrollIntoView({
                        behavior:
                            "smooth",

                        block:
                            "start"
                    });

                },
                300
            );
        }


    } catch (error) {

        // ====================================================
        // ERROR HANDLING
        // ====================================================

        console.error(
            "Sentilytics analysis error:",
            error
        );


        let errorMessage =
            "Unable to analyze the video.";


        if (
            error &&
            error.message
        ) {

            errorMessage =
                error.message;
        }


        showMessage(
            errorMessage,
            "error"
        );


    } finally {

        // ====================================================
        // ENABLE BUTTON AGAIN
        // ====================================================

        if (analyzeBtn) {

            analyzeBtn.disabled =
                false;


            analyzeBtn.innerHTML =
                "<span>Analyze Video</span><b>→</b>";
        }
    }
}


// ============================================================
// UPDATE VIDEO INFORMATION
// ============================================================

function updateVideoInfo(
    video
) {

    if (!video) {

        return;
    }


    const videoInfoCard =
        document.getElementById(
            "videoInfoCard"
        );


    const videoTitle =
        document.getElementById(
            "videoTitle"
        );


    const videoChannel =
        document.getElementById(
            "videoChannel"
        );


    const videoThumbnail =
        document.getElementById(
            "videoThumbnail"
        );


    const watchVideoLink =
        document.getElementById(
            "watchVideoLink"
        );


    // --------------------------------------------------------
    // Title
    // --------------------------------------------------------

    if (videoTitle) {

        videoTitle.textContent =
            video.title ||
            "YouTube Video";
    }


    // --------------------------------------------------------
    // Channel
    // --------------------------------------------------------

    if (videoChannel) {

        videoChannel.textContent =
            video.channel ||
            "Unknown Channel";
    }


    // --------------------------------------------------------
    // Thumbnail
    // --------------------------------------------------------

    if (videoThumbnail) {

        videoThumbnail.src =
            video.thumbnail ||
            "";


        videoThumbnail.alt =
            video.title ||
            "YouTube video thumbnail";
    }


    // --------------------------------------------------------
    // Watch link
    // --------------------------------------------------------

    if (watchVideoLink) {

        const currentVideoId =
            extractVideoId(
                videoUrl
                    ? videoUrl.value
                    : ""
            );


        if (currentVideoId) {

            watchVideoLink.href =
                `https://www.youtube.com/watch?v=${currentVideoId}`;
        }
    }


    // --------------------------------------------------------
    // Show video card
    // --------------------------------------------------------

    if (videoInfoCard) {

        videoInfoCard.hidden =
            false;
    }
}


// ============================================================
// UPDATE STATISTICS
// ============================================================

function updateStatistics(
    data
) {

    const counts =
        data.sentiment_counts ||
        {};


    const percentages =
        data.sentiment_percentages ||
        {};


    const total =
        Number(
            data.total_comments ||
            allComments.length ||
            0
        );


    // --------------------------------------------------------
    // Total comments
    // --------------------------------------------------------

    const totalComments =
        document.getElementById(
            "totalComments"
        );


    if (totalComments) {

        totalComments.textContent =
            formatNumber(
                total
            );
    }


    // --------------------------------------------------------
    // Positive count
    // --------------------------------------------------------

    const positiveCount =
        document.getElementById(
            "positiveCount"
        );


    if (positiveCount) {

        positiveCount.textContent =
            formatNumber(
                counts.positive ||
                0
            );
    }


    // --------------------------------------------------------
    // Negative count
    // --------------------------------------------------------

    const negativeCount =
        document.getElementById(
            "negativeCount"
        );


    if (negativeCount) {

        negativeCount.textContent =
            formatNumber(
                counts.negative ||
                0
            );
    }


    // --------------------------------------------------------
    // Neutral count
    // --------------------------------------------------------

    const neutralCount =
        document.getElementById(
            "neutralCount"
        );


    if (neutralCount) {

        neutralCount.textContent =
            formatNumber(
                counts.neutral ||
                0
            );
    }


    // --------------------------------------------------------
    // Positive percentage
    // --------------------------------------------------------

    const positivePercent =
        document.getElementById(
            "positivePercent"
        );


    if (positivePercent) {

        positivePercent.textContent =
            `${percentages.positive || 0}%`;
    }


    // --------------------------------------------------------
    // Negative percentage
    // --------------------------------------------------------

    const negativePercent =
        document.getElementById(
            "negativePercent"
        );


    if (negativePercent) {

        negativePercent.textContent =
            `${percentages.negative || 0}%`;
    }


    // --------------------------------------------------------
    // Neutral percentage
    // --------------------------------------------------------

    const neutralPercent =
        document.getElementById(
            "neutralPercent"
        );


    if (neutralPercent) {

        neutralPercent.textContent =
            `${percentages.neutral || 0}%`;
    }


    // --------------------------------------------------------
    // Progress bars
    // --------------------------------------------------------

    const positiveProgress =
        document.getElementById(
            "positiveProgress"
        );


    const negativeProgress =
        document.getElementById(
            "negativeProgress"
        );


    const neutralProgress =
        document.getElementById(
            "neutralProgress"
        );


    if (positiveProgress) {

        positiveProgress.style.width =
            `${percentages.positive || 0}%`;
    }


    if (negativeProgress) {

        negativeProgress.style.width =
            `${percentages.negative || 0}%`;
    }


    if (neutralProgress) {

        neutralProgress.style.width =
            `${percentages.neutral || 0}%`;
    }


    // --------------------------------------------------------
    // Overall sentiment
    // --------------------------------------------------------

    const sentimentScore =
        document.getElementById(
            "sentimentScore"
        );


    if (sentimentScore) {

        sentimentScore.textContent =
            formatSentiment(
                data.overall_sentiment
            );
    }


    // --------------------------------------------------------
    // Donut total
    // --------------------------------------------------------

    const donutTotal =
        document.getElementById(
            "donutTotal"
        );


    if (donutTotal) {

        donutTotal.textContent =
            formatNumber(
                total
            );
    }
}


// ============================================================
// FORMAT SENTIMENT
// ============================================================

function formatSentiment(
    sentiment
) {

    if (!sentiment) {

        return "Neutral";
    }


    return String(
        sentiment
    )
        .charAt(0)
        .toUpperCase()
        +
        String(
            sentiment
        )
            .slice(1)
            .toLowerCase();
}


// ============================================================
// RENDER COMMENTS
// ============================================================

function renderComments(
    comments
) {

    const container =
        document.getElementById(
            "commentsList"
        );


    if (!container) {

        return;
    }


    container.innerHTML =
        "";


    if (
        !Array.isArray(comments) ||
        !comments.length
    ) {

        container.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    💬
                </div>

                <h3>
                    No comments found
                </h3>

                <p>
                    This video has no public comments.
                </p>

            </div>

        `;


        return;
    }


    // --------------------------------------------------------
    // Create each comment
    // --------------------------------------------------------

    comments.forEach(
        function (comment) {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "comment";


            const sentiment =
                String(
                    comment.sentiment ||
                    "NEUTRAL"
                ).toUpperCase();


            let badgeClass =
                "badge-neutral";


            if (
                sentiment ===
                "POSITIVE"
            ) {

                badgeClass =
                    "badge-positive";

            } else if (
                sentiment ===
                "NEGATIVE"
            ) {

                badgeClass =
                    "badge-negative";
            }


            const likes =
                comment.likes ??
                comment.like_count ??
                0;


            const publishedAt =
                comment.published_at ||
                comment.publishedAt ||
                "";


            div.innerHTML = `

                <div class="comment-top">

                    <span class="author">
                        ${escapeHtml(
                            comment.author ||
                            "YouTube User"
                        )}
                    </span>

                    <span class="badge ${badgeClass}">
                        ${formatSentiment(
                            sentiment
                        )}
                    </span>

                </div>


                <div class="comment-text">

                    ${escapeHtml(
                        comment.text ||
                        ""
                    )}

                </div>


                <div class="comment-bottom">

                    <span>
                        👍 ${formatNumber(
                            likes
                        )}
                    </span>

                    <span>
                        ${formatDate(
                            publishedAt
                        )}
                    </span>

                </div>

            `;


            container.appendChild(
                div
            );
        }
    );
}


// ============================================================
// SEARCH / FILTER COMMENTS
// ============================================================

function displayComments() {

    const searchInput =
        document.getElementById(
            "searchComments"
        );


    if (!searchInput) {

        return;
    }


    const search =
        searchInput.value
            .toLowerCase()
            .trim();


    const filtered =
        allComments.filter(
            function (comment) {

                const text =
                    String(
                        comment.text ||
                        ""
                    ).toLowerCase();


                const author =
                    String(
                        comment.author ||
                        ""
                    ).toLowerCase();


                return (
                    text.includes(search) ||
                    author.includes(search)
                );
            }
        );


    renderComments(
        filtered
    );
}


// ============================================================
// FORMAT NUMBER
// ============================================================

function formatNumber(
    value
) {

    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {

        return "0";
    }


    return number.toLocaleString();
}


// ============================================================
// FORMAT DATE
// ============================================================

function formatDate(
    date
) {

    if (!date) {

        return "";
    }


    try {

        const parsedDate =
            new Date(date);


        if (
            Number.isNaN(
                parsedDate.getTime()
            )
        ) {

            return "";
        }


        return parsedDate.toLocaleDateString();


    } catch (error) {

        return "";
    }
}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(
    value
) {

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}


// ============================================================
// UPDATE CHARTS
// ============================================================

function updateCharts(
    data
) {

    // --------------------------------------------------------
    // Check Chart.js
    // --------------------------------------------------------

    if (
        typeof Chart ===
        "undefined"
    ) {

        console.warn(
            "Chart.js is not loaded. Charts skipped."
        );


        return;
    }


    const counts =
        data.sentiment_counts ||
        {};


    const positive =
        Number(
            counts.positive ||
            0
        );


    const negative =
        Number(
            counts.negative ||
            0
        );


    const neutral =
        Number(
            counts.neutral ||
            0
        );


    // ========================================================
    // DONUT CHART
    // ========================================================

    const donutCanvas =
        document.getElementById(
            "sentimentChart"
        );


    if (donutCanvas) {

        if (
            sentimentChartInstance
        ) {

            sentimentChartInstance.destroy();

            sentimentChartInstance =
                null;
        }


        sentimentChartInstance =
            new Chart(
                donutCanvas,
                {
                    type:
                        "doughnut",

                    data: {

                        labels: [
                            "Positive",
                            "Negative",
                            "Neutral"
                        ],

                        datasets: [

                            {
                                data: [
                                    positive,
                                    negative,
                                    neutral
                                ]
                            }

                        ]
                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        cutout:
                            "70%",

                        plugins: {

                            legend: {
                                display:
                                    false
                            }

                        }
                    }
                }
            );
    }


    // ========================================================
    // BAR CHART
    // ========================================================

    const trendCanvas =
        document.getElementById(
            "trendChart"
        );


    if (trendCanvas) {

        if (
            trendChartInstance
        ) {

            trendChartInstance.destroy();

            trendChartInstance =
                null;
        }


        trendChartInstance =
            new Chart(
                trendCanvas,
                {
                    type:
                        "bar",

                    data: {

                        labels: [
                            "Positive",
                            "Negative",
                            "Neutral"
                        ],

                        datasets: [

                            {
                                label:
                                    "Comments",

                                data: [
                                    positive,
                                    negative,
                                    neutral
                                ]
                            }

                        ]
                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {
                                display:
                                    false
                            }

                        },

                        scales: {

                            y: {

                                beginAtZero:
                                    true

                            }

                        }
                    }
                }
            );
    }
}


// ============================================================
// DARK / LIGHT MODE
// ============================================================

function toggleTheme() {

    // --------------------------------------------------------
    // Toggle DARK MODE
    // --------------------------------------------------------

    document.body.classList.toggle(
        "dark-mode"
    );


    // --------------------------------------------------------
    // Check current theme
    // --------------------------------------------------------

    const isDark =
        document.body.classList.contains(
            "dark-mode"
        );


    // --------------------------------------------------------
    // Save preference
    // --------------------------------------------------------

    localStorage.setItem(
        "sentilyticsTheme",
        isDark
            ? "dark"
            : "light"
    );


    // --------------------------------------------------------
    // Update button
    // --------------------------------------------------------

    updateThemeButton();


    console.log(
        "Theme changed:",
        isDark
            ? "Dark Mode"
            : "Light Mode"
    );
}


// ============================================================
// UPDATE THEME BUTTON
// ============================================================

function updateThemeButton() {

    const themeBtn =
        document.getElementById(
            "themeBtn"
        );


    if (!themeBtn) {

        return;
    }


    const isDark =
        document.body.classList.contains(
            "dark-mode"
        );


    if (isDark) {

        themeBtn.innerHTML =
            "☀️ <span>Light Mode</span>";

    } else {

        themeBtn.innerHTML =
            "🌙 <span>Dark Mode</span>";
    }
}


// ============================================================
// LOAD SAVED THEME
// ============================================================

function loadTheme() {

    const savedTheme =
        localStorage.getItem(
            "sentilyticsTheme"
        );


    if (
        savedTheme ===
        "dark"
    ) {

        document.body.classList.add(
            "dark-mode"
        );

    } else {

        document.body.classList.remove(
            "dark-mode"
        );
    }


    updateThemeButton();
}


// ============================================================
// SIDEBAR TOGGLE
// ============================================================

function toggleSidebar() {

    const sidebar =
        document.getElementById(
            "sidebar"
        );


    if (sidebar) {

        sidebar.classList.toggle(
            "open"
        );
    }
}


// ============================================================
// DEMO DATA
// ============================================================

function loadDemo() {

    const demoComments = [

        {
            author:
                "Demo User 1",

            text:
                "Amazing video! Very helpful.",

            likes:
                15,

            sentiment:
                "POSITIVE",

            published_at:
                new Date().toISOString()
        },


        {
            author:
                "Demo User 2",

            text:
                "The explanation was very clear.",

            likes:
                8,

            sentiment:
                "POSITIVE",

            published_at:
                new Date().toISOString()
        },


        {
            author:
                "Demo User 3",

            text:
                "I think the video was okay.",

            likes:
                3,

            sentiment:
                "NEUTRAL",

            published_at:
                new Date().toISOString()
        },


        {
            author:
                "Demo User 4",

            text:
                "The information was confusing.",

            likes:
                2,

            sentiment:
                "NEGATIVE",

            published_at:
                new Date().toISOString()
        }

    ];


    allComments =
        demoComments;


    const total =
        demoComments.length;


    const positive =
        demoComments.filter(
            function (comment) {

                return (
                    comment.sentiment ===
                    "POSITIVE"
                );

            }
        ).length;


    const negative =
        demoComments.filter(
            function (comment) {

                return (
                    comment.sentiment ===
                    "NEGATIVE"
                );

            }
        ).length;


    const neutral =
        demoComments.filter(
            function (comment) {

                return (
                    comment.sentiment ===
                    "NEUTRAL"
                );

            }
        ).length;


    const demoData = {

        total_comments:
            total,

        overall_sentiment:
            "POSITIVE",

        sentiment_counts: {

            positive:
                positive,

            negative:
                negative,

            neutral:
                neutral

        },

        sentiment_percentages: {

            positive:
                Math.round(
                    positive /
                    total *
                    100
                ),

            negative:
                Math.round(
                    negative /
                    total *
                    100
                ),

            neutral:
                Math.round(
                    neutral /
                    total *
                    100
                )

        }

    };


    updateStatistics(
        demoData
    );


    renderComments(
        allComments
    );


    updateCharts(
        demoData
    );


    showMessage(
        "Demo data loaded successfully.",
        "success"
    );


    // --------------------------------------------------------
    // Scroll to comments/results
    // --------------------------------------------------------

    const commentsSection =
        document.querySelector(
            ".comments-section"
        );


    if (commentsSection) {

        setTimeout(
            function () {

                commentsSection.scrollIntoView({
                    behavior:
                        "smooth",

                    block:
                        "start"
                });

            },
            300
        );
    }
}


// ============================================================
// SINGLE COMMENT ANALYSIS
// GROQ AI + MULTILINGUAL SUPPORT
// ============================================================

async function analyzeSingleComment() {

    const input =
        document.getElementById(
            "singleComment"
        );


    const result =
        document.getElementById(
            "singleResult"
        );


    // --------------------------------------------------------
    // Check elements
    // --------------------------------------------------------

    if (
        !input ||
        !result
    ) {

        console.error(
            "singleComment or singleResult element not found."
        );


        return;
    }


    // --------------------------------------------------------
    // Get comment text
    // --------------------------------------------------------

    const text =
        input.value.trim();


    // --------------------------------------------------------
    // Check empty comment
    // --------------------------------------------------------

    if (!text) {

        result.innerHTML = `

            <div class="single-result">

                <strong>
                    ⚠️ Please enter a comment.
                </strong>

            </div>

        `;


        return;
    }


    // --------------------------------------------------------
    // Show AI loading message
    // --------------------------------------------------------

    result.innerHTML = `

        <div class="single-result">

            <strong>
                🤖 AI Analyzing...
            </strong>

            <p>
                Groq AI is analyzing the comment.
            </p>

        </div>

    `;


    try {

        console.log(
            "Sending comment to Groq AI..."
        );


        // ====================================================
        // CALL FLASK BACKEND
        // ====================================================

        const response =
            await fetch(
                `${API_BASE_URL}/api/analyze-comment`,
                {
                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            comment:
                                text

                        })
                }
            );


        // ====================================================
        // READ RESPONSE
        // ====================================================

        let data;


        try {

            data =
                await response.json();

        } catch (jsonError) {

            console.error(
                "Invalid JSON response:",
                jsonError
            );


            throw new Error(
                "Backend returned an invalid response."
            );
        }


        console.log(
            "Single comment AI response:",
            data
        );


        // ====================================================
        // CHECK HTTP ERROR
        // ====================================================

        if (!response.ok) {

            throw new Error(
                data.error ||
                `Backend error: ${response.status}`
            );
        }


        // ====================================================
        // CHECK APPLICATION ERROR
        // ====================================================

        if (
            data.success === false
        ) {

            throw new Error(
                data.error ||
                "AI analysis failed."
            );
        }


        // ====================================================
        // GET SENTIMENT
        // ====================================================

        const sentiment =
            String(
                data.sentiment ||
                "NEUTRAL"
            )
                .trim()
                .toUpperCase();


        // ====================================================
        // ALLOW ONLY VALID SENTIMENTS
        // ====================================================

        const validSentiments = [

            "POSITIVE",
            "NEGATIVE",
            "NEUTRAL"

        ];


        if (
            !validSentiments.includes(
                sentiment
            )
        ) {

            throw new Error(
                "AI returned an invalid sentiment."
            );
        }


        // ====================================================
        // SENTIMENT EMOJI
        // ====================================================

        let emoji =
            "😐";


        if (
            sentiment ===
            "POSITIVE"
        ) {

            emoji =
                "😊";

        } else if (
            sentiment ===
            "NEGATIVE"
        ) {

            emoji =
                "😞";
        }


        // ====================================================
        // DISPLAY RESULT
        // ====================================================

        result.innerHTML = `

            <div class="single-result">

                <strong>

                    ${emoji}

                    ${formatSentiment(
                        sentiment
                    )}

                </strong>


                <p>

                    ${escapeHtml(
                        text
                    )}

                </p>


                <small>

                    🤖 Analyzed by Groq AI
                    • Multilingual Analysis

                </small>

            </div>

        `;


        console.log(
            "AI sentiment:",
            sentiment
        );


    } catch (error) {

        // ====================================================
        // ERROR HANDLING
        // ====================================================

        console.error(
            "Single comment analysis error:",
            error
        );


        const errorText =
            error &&
            error.message
                ? error.message
                : "Unable to analyze the comment.";


        result.innerHTML = `

            <div class="single-result">

                <strong>
                    ❌ Analysis Failed
                </strong>


                <p>
                    ${escapeHtml(
                        errorText
                    )}
                </p>

            </div>

        `;
    }
}


// ============================================================
// ENTER KEY SUPPORT
// ============================================================

if (videoUrl) {

    videoUrl.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key ===
                "Enter"
            ) {

                event.preventDefault();

                analyzeVideo();
            }
        }
    );
}


// ============================================================
// PAGE INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        // ----------------------------------------------------
        // Load saved theme
        // ----------------------------------------------------

        loadTheme();


        // ----------------------------------------------------
        // Check backend
        // ----------------------------------------------------

        checkBackend();


        console.log(
            "Sentilytics initialized successfully."
        );
    }
);


// ============================================================
// GLOBAL FUNCTION SAFETY
// ============================================================

// These make functions available to
// inline HTML onclick attributes.

window.analyzeVideo =
    analyzeVideo;


window.toggleTheme =
    toggleTheme;


window.toggleSidebar =
    toggleSidebar;


window.loadDemo =
    loadDemo;


window.analyzeSingleComment =
    analyzeSingleComment;


window.displayComments =
    displayComments;


// ------------------------------------------------------------
// Safe filterComments reference
// ------------------------------------------------------------

if (
    typeof filterComments ===
    "function"
) {

    window.filterComments =
        filterComments;
}


// ============================================================
// FINAL LOAD MESSAGE
// ============================================================

console.log(
    "Sentilytics app.js loaded successfully."
);

console.log(
    "Multilingual single-comment AI analysis: ENABLED"
);