let optimisticCart = JSON.parse(localStorage.getItem("optimisticCart")) || JSON.parse(localStorage.getItem("legacyCart")) || [];
let optimisticProduct = JSON.parse(localStorage.getItem("openedProduct"));

function addtocart() {
    optimisticCart.push(optimisticProduct);
    localStorage.setItem("optimisticCart", JSON.stringify(optimisticCart));
    localStorage.setItem("legacyCart", JSON.stringify(optimisticCart));
    const {qty,price,productTitle} = optimisticProduct;
    alert(`${qty} quantities of this product has been added to cart.`);
    history.back();
}

function separator(numb) {
    var str = numb.toString().split(".");
    str[0] = str[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return str.join(".");
}

let { id, productTitle, price, productImg, qty } = optimisticProduct;

document.querySelector("#productImage>img").src = productImg[0];

productImg.forEach((img) => {
    let prodimg = document.createElement("img");
    prodimg.onclick = () => {
        document.querySelector("#productImage>img").src = img;
    }   
    prodimg.src = img;
    document.querySelector("#multiImage").append(prodimg);
});

document.querySelector("#title").textContent = productTitle;

document.querySelector("#price").textContent = "Price : ₹ " + separator(price) + "/-";

document.querySelector("#qtyDiv>input").value = qty;

function decQty() {
    let quantity = document.querySelector("#qtyDiv>input").value
    if (quantity > 1) {
        document.querySelector("#qtyDiv>input").value = --quantity;
        document.querySelector("#pieces").textContent = quantity + " pieces";
        document.querySelector("#item-amount").textContent = "₹" + separator((quantity * price).toFixed(2));
        document.querySelector("#showtotal").textContent = "₹" + (quantity * price + 11700.63).toFixed(2);
        optimisticProduct.qty = quantity;
        localStorage.setItem("openedProduct", JSON.stringify(optimisticProduct));
    }
}
function incQty() {
    let quantity = document.querySelector("#qtyDiv>input").value;
    document.querySelector("#qtyDiv>input").value = ++quantity;
    document.querySelector("#pieces").textContent = quantity + " pieces";
    document.querySelector("#item-amount").textContent = "₹" + (quantity * price).toFixed(2);
    document.querySelector("#showtotal").textContent = "₹" + (quantity * price + 11700.63).toFixed(2);
    optimisticProduct.qty = quantity;
    localStorage.setItem("openedProduct", JSON.stringify(optimisticProduct));
}

let quantity = document.querySelector("#qtyDiv>input").value;
document.querySelector("#pieces").textContent = quantity + " pieces";
document.querySelector("#item-amount").textContent = "₹" + (quantity * price).toFixed(2);
document.querySelector("#showtotal").textContent = "₹" + (quantity * price + 11700.63).toFixed(2);