const app = Vue.createApp({
    data() {
        return {
            hoursToShow: 6,
            refreshSeconds: 30,
            running: true,
            configDiv: null,
            refreshSecondsDiv: null,
            polling: null,
            sensor_data: null
        }
    },
    methods: {
        timeSpanChanged() {
            this.fetchNewData();
        },
        gotNewData(stationData) {
            var processingDurationMs;
            this.configDiv.style.backgroundColor = "white";
    
            // Check if we can keep up with this fetch rate, or increase interval by 50ms if not.        
            processingDurationMs = new Date() - this.fetchStartMs;
            this.refreshSecondsDiv.style.backgroundColor = (processingDurationMs > 1000 * this.refreshSeconds) ? "#FF7777" : "#FFFFFF";

            this.sensor_data = stationData;

            // Schedule next call with the requested interval minus the time needed to process the previous call
            // Note that contrary to setInterval, this technique guarantees that we will never have 
            // several fetch in parallel in case we can't keep up with the requested interval
            var waitingDelayMs = 1000 * this.refreshSeconds - processingDurationMs;
            console.log('Processing delay: ' + processingDurationMs + ' waiting: ' + waitingDelayMs);
            if (this.running) {
                this.polling = window.setTimeout(this.fetchNewData, (waitingDelayMs > 0)?waitingDelayMs:0);
            }
        },
        fetchError(error) {
            this.configDiv.style.backgroundColor = "red";
            console.log("ERROR: " + error);
            // Also schedule next call in case of error
            var waitingDelayMs = 1000 * this.refreshSeconds - (new Date() - this.fetchStartMs);
            this.polling = window.setTimeout(this.fetchNewData, (waitingDelayMs > 0)?waitingDelayMs:0);
        },
        fetchNewData() {
            if (!this.running) {
                return;
            }
            this.fetchStartMs = Date.now();

            var secondsToFetch = Math.floor(parseFloat(document.getElementById("hoursToShow").value) * 3600);
            var uri = "/sensorData?maxAgeSeconds=" + secondsToFetch;  // 24 hours
            axios.
                get(uri).
                then(response => this.gotNewData(response.data)).
                catch(error => this.fetchError(error));
        },
        onPauseResume() {
            this.running = !this.running;
        }
    },
    mounted () {
        this.configDiv = document.getElementById("config");
        this.refreshSecondsDiv = document.getElementById("refreshSeconds");
        this.fetchNewData();
    },
    beforeUnmount () {
        window.clearTimeout(this.polling);
    }
})