const app = Vue.createApp({
    data() {
        return {
            hoursToShow: 6,
            refreshSeconds: 30,
            running: true,
            configDiv: null,
            periodField: null,
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
            this.periodField.style.backgroundColor = (processingDurationMs > 1000 * parseInt(this.periodField.value))?"#FF7777":"#FFFFFF";

            this.sensor_data = stationData;

            // Schedule next call with the requested interval minus the time needed to process the previous call
            // Note that contrary to setInterval, this technique guarantees that we will never have 
            // several fetch in parallel in case we can't keep up with the requested interval
            var waitingDelayMs = 1000 * parseInt(this.periodField.value) - processingDurationMs;
            console.log('Processing delay: ' + processingDurationMs + ' waiting: ' + waitingDelayMs);
            if (this.running) {
                this.polling = window.setTimeout(this.fetchNewData, (waitingDelayMs > 0)?waitingDelayMs:0);
            }
        },
        fetchError(error) {
            this.configDiv.style.backgroundColor = "red";
            console.log("ERROR: " + error);
            // Also schedule next call in case of error
            var waitingDelayMs = 1000 * parseInt(this.periodField.value) - (new Date() - this.fetchStartMs);
            this.polling = window.setTimeout(this.fetchNewData, (waitingDelayMs > 0)?waitingDelayMs:0);
        },
        fetchNewData() {
            if (!this.running) {
                return;
            }
            this.fetchStartMs = Date.now();

            var secondsToFetch = Math.floor(parseFloat(document.getElementById("maxSamplesField").value) * 3600);
            var uri = "/sensorData?maxAgeSeconds=" + secondsToFetch;  // 24 hours
            axios.
                get(uri).
                then(response => this.gotNewData(response.data)).
                catch(error => this.fetchError(error));
        },
        onPauseStart() {
            this.running = !this.running;
        }
    },
    mounted () {
        this.configDiv = document.getElementById("config");
        this.periodField = document.getElementById("periodField");
        this.fetchNewData();
    },
    beforeUnmount () {
        window.clearTimeout(this.polling);
    }
})