
function getCsrfToken() {
  return document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute('content');
}


function switchPaymentMethod(type, content) {
    const stripeCard = document.getElementById('stripe-card');
    const stripePaymentElement = document.getElementById('payment-element');
    const paypalCard = document.getElementById('paypal-card');

    if (type === 'stripe') {
    paypalCard.style.display = 'none'
    stripeCard.style.display = 'block'
    paypalCard.innerHTML = ''
    } else {
    stripeCard.style.display = 'none'
    paypalCard.style.display = 'block'
    stripePaymentElement.innerHTML = ''
    paypalCard.innerHTML = content
    }
}


async function createPaypalSession() {

    const headers = {
        'Content-Type' : 'application/json',
        'X-CSRFToken' : getCsrfToken(),
    }

    try {

        const appointmentElement = document.getElementById('appointment-id');
        const appointmentId = appointmentElement.getAttribute('data-appointment-id');

        const { data } = await axios.post(
            `/transaction/paypal/${appointmentId}/`,
            {}, // empty request body
            { headers }
        );
        switchPaymentMethod('paypal', data)
   } catch (e) {
        notyf.error(e?.response?.data?.message ||
        "An error occurred while creating a stripe session.");
   }
}