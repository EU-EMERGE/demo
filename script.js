// Funzione per caricare un file JSON
function loadJSON(file, callback) {
    let xhttp = new XMLHttpRequest();
    xhttp.open("GET", file, true);
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            callback(JSON.parse(this.responseText));
        }
    };
    xhttp.send();
}

// Neural network configuration
let config = null;
let canvas = document.getElementById('networkCanvas');
let ctx = canvas.getContext('2d');
let neurons = [];

// Function to draw the static structure of the network
function drawStaticNetwork() {
    canvas.width = window.innerWidth * 0.8;
    canvas.height = window.innerHeight * 0.8;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let layerWidth = canvas.width / (config.layers.length + 1);
    let maxNeurons = Math.max(...config.layers); // Get the maximum number of neurons in any layer
    neurons = []; // Reset neurons array

    for (let i = 0; i < config.layers.length; i++) {
        let numNeurons = config.layers[i]; // Number of neurons in the current layer
        let layerHeight = canvas.height / (maxNeurons + 1);
        let layerVerticalOffset = (canvas.height - (numNeurons * layerHeight)) / 2;

        for (let j = 0; j < numNeurons; j++) {
            let neuronX = (i + 1) * layerWidth;
            let neuronY = layerVerticalOffset + (j + 1) * layerHeight;

            // Draw the neuron (base gray color)
            ctx.beginPath();
            ctx.arc(neuronX, neuronY, 20, 0, Math.PI * 2);
            ctx.fillStyle = "#888"; // Base color (gray)
            ctx.fill();
            ctx.lineWidth = 2;
            ctx.strokeStyle = "#000";
            ctx.stroke();

            neurons.push({ x: neuronX, y: neuronY, layer: i, id: j });

            // Draw input/output arrows
            if (i === 0) {
                drawInputArrow(neuronX, neuronY);
            } else if (i === config.layers.length - 1) {
                drawOutputArrow(neuronX, neuronY);
            }
        }
    }

    // Draw the edges (connections) between neurons
    for (let i = 0; i < neurons.length; i++) {
        let neuron = neurons[i];
        if (neuron.layer < config.layers.length - 1) {
            let nextLayerNeurons = neurons.filter(n => n.layer === neuron.layer + 1);
            for (let nextNeuron of nextLayerNeurons) {
                ctx.beginPath();
                ctx.moveTo(neuron.x, neuron.y);
                ctx.lineTo(nextNeuron.x, nextNeuron.y);
                ctx.lineWidth = 1;
                ctx.strokeStyle = "#ccc"; // Light gray color for edges
                ctx.stroke();
            }
        }
    }
}

// Function to draw input arrows
function drawInputArrow(neuronX, neuronY) {
    ctx.beginPath();
    ctx.moveTo(neuronX - 50, neuronY);
    ctx.lineTo(neuronX - 20, neuronY);
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#ccc"; // Match connection color
    ctx.stroke();

    // Draw arrowhead
    ctx.beginPath();
    ctx.moveTo(neuronX - 25, neuronY - 5);
    ctx.lineTo(neuronX - 20, neuronY);
    ctx.lineTo(neuronX - 25, neuronY + 5);
    ctx.fillStyle = "#ccc"; // Match connection color
    ctx.fill();
}

// Function to draw output arrows
function drawOutputArrow(neuronX, neuronY) {
    ctx.beginPath();
    ctx.moveTo(neuronX + 20, neuronY);
    ctx.lineTo(neuronX + 50, neuronY);
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#ccc"; // Match connection color
    ctx.stroke();

    // Draw arrowhead
    ctx.beginPath();
    ctx.moveTo(neuronX + 45, neuronY - 5);
    ctx.lineTo(neuronX + 50, neuronY);
    ctx.lineTo(neuronX + 45, neuronY + 5);
    ctx.fillStyle = "#ccc"; // Match connection color
    ctx.fill();
}

// Function to update neuron activations and change their colors
function updateNeuronColors(activations) {
    for (let i = 0; i < neurons.length; i++) {
        let neuron = neurons[i];
        let activationValue = activations[neuron.layer][neuron.id];

        // Ensure activationValue is valid
        if (isNaN(activationValue) || activationValue < 0) {
            activationValue = 0; // Default to 0 if invalid
        }

        let intensity = Math.min(1, Math.max(0, activationValue)); // Clamp intensity between 0 and 1
        let color = intensityToCoolWarm(intensity);

        // Change the neuron's color based on the activation
        ctx.beginPath();
        ctx.arc(neuron.x, neuron.y, 20, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#000";
        ctx.stroke();
    }
}

// Function to convert a normalized intensity (0 to 1) to a "coolwarm" color palette
function intensityToCoolWarm(intensity) {
    let norm = Math.min(1, Math.max(0, intensity)); // Ensure intensity is between 0 and 1
    let r, g, b;

    if (norm < 0.5) {
        // Interpolating blue -> white
        r = Math.floor(255 * (2 * norm));
        g = Math.floor(255 * (2 * norm));
        b = 255;
    } else {
        // Interpolating white -> red
        r = 255;
        g = Math.floor(255 * (2 - 2 * norm));
        b = Math.floor(255 * (2 - 2 * norm));
    }

    return `rgb(${r}, ${g}, ${b})`;
}

// Load configuration and initialize the network
loadJSON('config.json', function (data) {
    config = data;
    drawStaticNetwork(); // Draw the static structure of the network
});

// Update activations periodically
function updateActivationsPeriodically() {
    loadJSON("activations.json", data => {
        updateNeuronColors(data); // Update only the neuron colors
        requestAnimationFrame(updateActivationsPeriodically); // Schedule the next update
    });
}

// Start the periodic updates
updateActivationsPeriodically();