let items = JSON.parse(localStorage.getItem("optimisticCart")) || JSON.parse(localStorage.getItem("legacyCart")) || [];
if (!Array.isArray(items) || items.length === 0) {
    const left = document.querySelector("#left");
    if (left) {
        left.innerHTML = '<div style="padding:24px;border:1px dashed rgba(255,255,255,.2);border-radius:12px;color:#94a3b8;">Your cart is empty. Browse products and add items.</div>';
    }
    const total = document.querySelector("#totalamount");
    if (total) total.textContent = "ZMW 0.00";
}

displayitems(items);

let totalamount = 0;
total(items);

function separator(numb) {
    var str = numb.toString().split(".");
    str[0] = str[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return str.join(".");
}

function total(items) {
    totalamount = items.reduce((sum, ele) => {
        return sum + (ele.qty * ele.price);
    }, 0);
    document.querySelector("#totalamount").textContent = "ZMW " + separator(totalamount.toFixed(2));
}


function displayitems(items) {
    let location = document.querySelector("#left");
    location.innerHTML = null;

    items.forEach(({ productTitle, productImg, price, qty }, index) => {
        let card = document.createElement("div");

        let imagediv = document.createElement("div");
        let image = document.createElement("img");
        image.src = Array.isArray(productImg) && productImg.length ? productImg[0] : '';
        image.alt = productTitle || 'Product';
        imagediv.append(image);


        let desdiv = document.createElement("div");
        let title = document.createElement("p");
        title.textContent = productTitle;

        let removebtndiv = document.createElement("div");
        removebtndiv.setAttribute("class", "removesym");
        removebtndiv.innerHTML = `<i class="fas fa-times"></i>`;

        let pricediv = document.createElement("div");
        let priceperpiece = document.createElement("p");
        priceperpiece.textContent = separator(price);

        let qtydiv = document.createElement("div");
        qtydiv.setAttribute("class", "qtydiv");

        let decP = document.createElement("p");
        decP.textContent = "-";
        let decdiv = document.createElement("div");
        decdiv.append(decP);
        decdiv.onclick = () => {
            if (qtyinput.value <= 1) {
                items = items.filter((ele) => {
                    return ele != items[index];
                });
                localStorage.setItem("optimisticCart", JSON.stringify(items));
                localStorage.setItem("legacyCart", JSON.stringify(items));
                displayitems(items);
                if (items.length==0) {
                    alert("Your cart is empty");
                    history.back();
                }
                return;
            }
            qtyinput.value--;
            subtotal.textContent = "Subtotal : ZMW " + separator((qtyinput.value * price).toFixed(2));
            items[index].qty = qtyinput.value;
            localStorage.setItem("optimisticCart", JSON.stringify(items));
            localStorage.setItem("legacyCart", JSON.stringify(items));
            total(items);
        }

        let incP = document.createElement("p");
        incP.textContent = "+";
        let incdiv = document.createElement("div");
        incdiv.append(incP);
        incdiv.onclick = () => {
            qtyinput.value++;
            subtotal.textContent = "Subtotal : ZMW " + separator((qtyinput.value * price).toFixed(2));
            items[index].qty = qtyinput.value;
            localStorage.setItem("optimisticCart", JSON.stringify(items));
            localStorage.setItem("legacyCart", JSON.stringify(items));
            total(items);
        }

        let qtyinput = document.createElement("input");
        qtyinput.value = qty;


        let perprice = document.createElement("p");
        perprice.textContent = `ZMW ${separator(price)} (Per Piece)`;

        qtydiv.append(perprice, decdiv, qtyinput, incdiv);



        let subtotal = document.createElement("p");
        subtotal.textContent = "Subtotal : ZMW " + separator((qtyinput.value * price).toFixed(2));

        desdiv.append(removebtndiv, title, pricediv, qtydiv, subtotal);

        card.append(imagediv, desdiv);
        location.append(card);

        removebtndiv.firstChild.onclick = () => {
            items = items.filter((ele) => {
                return ele != items[index];
            });
            localStorage.setItem("optimisticCart", JSON.stringify(items));
            localStorage.setItem("legacyCart", JSON.stringify(items));
            displayitems(items);
            total(items);
            if (items.length==0) {
                alert("Your cart is empty");
                history.back();
            }
        }
    });
}