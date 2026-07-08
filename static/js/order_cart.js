(function () {
  'use strict';

  function formatMoney(amount) {
    return '$' + Number(amount || 0).toFixed(2);
  }

  function parseMoney(value) {
    var n = parseFloat(value);
    return isNaN(n) ? 0 : n;
  }

  window.OrderCart = {
    formatMoney: formatMoney,
    parseMoney: parseMoney,

    initOrderForm: function () {
      var form = document.getElementById('orderForm');
      if (!form) return;

      var rows = form.querySelectorAll('.order-product-row');
      var subtotalEl = document.getElementById('orderSubtotal');
      var taxEl = document.getElementById('orderTax');
      var discountEl = document.getElementById('orderDiscount');
      var grandTotalEl = document.getElementById('orderGrandTotal');
      var stockAlert = document.getElementById('orderStockAlert');

      function getRowData(row) {
        return {
          row: row,
          checkbox: row.querySelector('.product-select'),
          qtyInput: row.querySelector('.qty-input'),
          price: parseFloat(row.dataset.price || '0'),
          stock: parseInt(row.dataset.stock || '0', 10),
          lineSubtotalEl: row.querySelector('.line-subtotal'),
          stockWarning: row.querySelector('.stock-warning'),
        };
      }

      function setQty(rowData, qty) {
        qty = Math.max(1, parseInt(qty, 10) || 1);
        rowData.qtyInput.value = qty;
        return qty;
      }

      function validateRow(rowData) {
        var qty = parseInt(rowData.qtyInput.value, 10) || 0;
        var selected = rowData.checkbox.checked;
        var overStock = selected && qty > rowData.stock;

        rowData.row.classList.toggle('selected', selected);
        rowData.row.classList.toggle('stock-error', overStock);

        if (rowData.stockWarning) {
          rowData.stockWarning.textContent = overStock
            ? 'Insufficient stock available.'
            : '';
          rowData.stockWarning.classList.toggle('d-none', !overStock);
        }

        var lineTotal = selected ? rowData.price * qty : 0;
        if (rowData.lineSubtotalEl) {
          rowData.lineSubtotalEl.textContent = formatMoney(lineTotal);
        }

        return !overStock;
      }

      function recalculate() {
        var subtotal = 0;
        var valid = true;

        rows.forEach(function (row) {
          var data = getRowData(row);
          if (!validateRow(data)) valid = false;
          if (data.checkbox.checked) {
            var qty = parseInt(data.qtyInput.value, 10) || 0;
            subtotal += data.price * qty;
          }
        });

        var tax = parseMoney(taxEl ? taxEl.value : 0);
        var discount = parseMoney(discountEl ? discountEl.value : 0);
        var grand = Math.max(subtotal + tax - discount, 0);

        if (subtotalEl) subtotalEl.textContent = formatMoney(subtotal);
        if (grandTotalEl) grandTotalEl.textContent = formatMoney(grand);

        if (stockAlert) {
          stockAlert.classList.toggle('d-none', valid);
        }

        return valid;
      }

      rows.forEach(function (row) {
        var data = getRowData(row);

        row.querySelectorAll('.qty-minus').forEach(function (btn) {
          btn.addEventListener('click', function () {
            if (!data.checkbox.checked) data.checkbox.checked = true;
            setQty(data, (parseInt(data.qtyInput.value, 10) || 1) - 1);
            recalculate();
          });
        });

        row.querySelectorAll('.qty-plus').forEach(function (btn) {
          btn.addEventListener('click', function () {
            if (!data.checkbox.checked) data.checkbox.checked = true;
            var next = (parseInt(data.qtyInput.value, 10) || 1) + 1;
            if (next <= data.stock) {
              setQty(data, next);
            }
            recalculate();
          });
        });

        data.qtyInput.addEventListener('input', function () {
          if (!data.checkbox.checked) data.checkbox.checked = true;
          recalculate();
        });

        data.checkbox.addEventListener('change', recalculate);
      });

      [taxEl, discountEl].forEach(function (el) {
        if (el) el.addEventListener('input', recalculate);
      });

      form.addEventListener('submit', function (e) {
        if (!recalculate()) {
          e.preventDefault();
          if (stockAlert) stockAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });

      recalculate();
    },

    initPos: function (products, placeholderImage) {
      var form = document.getElementById('posCheckoutForm');
      var cartBody = document.getElementById('cart-table-body');
      var barcodeInput = document.getElementById('barcode-input');
      var searchResults = document.getElementById('search-results');
      var subtotalEl = document.getElementById('summary-subtotal');
      var discountEl = document.getElementById('discount-input');
      var taxEl = document.getElementById('tax-input');
      var grandTotalEl = document.getElementById('summary-total');
      var amountPaidEl = document.getElementById('amount-paid');
      var changeEl = document.getElementById('change-due');
      var checkoutBtn = document.getElementById('btn-checkout');
      var clearBtn = document.getElementById('btn-clear-cart');
      var stockAlert = document.getElementById('posStockAlert');
      var productGrid = document.getElementById('pos-product-grid');

      var cart = {};
      var productMap = {};
      products.forEach(function (p) { productMap[p.id] = p; });

      function cartItems() {
        return Object.keys(cart).map(function (id) {
          return { product: productMap[id], qty: cart[id] };
        }).filter(function (item) { return item.product; });
      }

      function addToCart(productId, qty) {
        var product = productMap[productId];
        if (!product) return;
        var current = cart[productId] || 0;
        var next = current + (qty || 1);
        if (next > product.stock) {
          if (stockAlert) {
            stockAlert.textContent = 'Insufficient stock available for ' + product.name + '. Available: ' + product.stock + '.';
            stockAlert.classList.remove('d-none');
          }
          next = product.stock;
        } else if (stockAlert) {
          stockAlert.classList.add('d-none');
        }
        if (next <= 0) {
          delete cart[productId];
        } else {
          cart[productId] = next;
        }
        renderCart();
      }

      function setCartQty(productId, qty) {
        var product = productMap[productId];
        if (!product) return;
        qty = parseInt(qty, 10) || 0;
        if (qty <= 0) {
          delete cart[productId];
        } else if (qty > product.stock) {
          if (stockAlert) {
            stockAlert.textContent = 'Insufficient stock available for ' + product.name + '. Available: ' + product.stock + '.';
            stockAlert.classList.remove('d-none');
          }
          cart[productId] = product.stock;
        } else {
          if (stockAlert) stockAlert.classList.add('d-none');
          cart[productId] = qty;
        }
        renderCart();
      }

      function renderCart() {
        cartBody.innerHTML = '';
        var subtotal = 0;
        var items = cartItems();

        items.forEach(function (item) {
          var lineTotal = item.product.price * item.qty;
          subtotal += lineTotal;
          var imgSrc = item.product.image || placeholderImage;
          var tr = document.createElement('tr');
          tr.innerHTML =
            '<td><div class="d-flex align-items-center gap-2">' +
              '<img src="' + imgSrc + '" alt="" style="width:36px;height:36px;object-fit:cover;border-radius:6px">' +
              '<div><div class="fw-semibold">' + item.product.name + '</div>' +
              '<small class="text-muted">SKU: ' + item.product.sku + '</small></div></div></td>' +
            '<td>' + formatMoney(item.product.price) + '</td>' +
            '<td><div class="qty-control">' +
              '<button type="button" class="cart-minus" data-id="' + item.product.id + '">−</button>' +
              '<input type="number" class="cart-qty" data-id="' + item.product.id + '" value="' + item.qty + '" min="1" max="' + item.product.stock + '">' +
              '<button type="button" class="cart-plus" data-id="' + item.product.id + '">+</button>' +
            '</div></td>' +
            '<td class="fw-bold text-success">' + formatMoney(lineTotal) + '</td>' +
            '<td><button type="button" class="btn btn-sm btn-outline-danger cart-remove" data-id="' + item.product.id + '"><i class="bi bi-trash"></i></button></td>';
          cartBody.appendChild(tr);
        });

        var discount = parseMoney(discountEl ? discountEl.value : 0);
        var tax = parseMoney(taxEl ? taxEl.value : 0);
        var grand = Math.max(subtotal + tax - discount, 0);

        if (subtotalEl) subtotalEl.textContent = formatMoney(subtotal);
        if (grandTotalEl) grandTotalEl.textContent = formatMoney(grand);

        var paid = parseMoney(amountPaidEl ? amountPaidEl.value : 0);
        if (changeEl) changeEl.textContent = formatMoney(Math.max(paid - grand, 0));

        if (checkoutBtn) checkoutBtn.disabled = items.length === 0;

        cartBody.querySelectorAll('.cart-minus').forEach(function (btn) {
          btn.addEventListener('click', function () {
            var id = btn.dataset.id;
            setCartQty(id, (cart[id] || 1) - 1);
          });
        });
        cartBody.querySelectorAll('.cart-plus').forEach(function (btn) {
          btn.addEventListener('click', function () {
            var id = btn.dataset.id;
            setCartQty(id, (cart[id] || 0) + 1);
          });
        });
        cartBody.querySelectorAll('.cart-qty').forEach(function (input) {
          input.addEventListener('change', function () {
            setCartQty(input.dataset.id, input.value);
          });
        });
        cartBody.querySelectorAll('.cart-remove').forEach(function (btn) {
          btn.addEventListener('click', function () {
            delete cart[btn.dataset.id];
            renderCart();
          });
        });
      }

      if (productGrid) {
        products.forEach(function (p) {
          var tile = document.createElement('button');
          tile.type = 'button';
          tile.className = 'pos-product-tile border-0';
          tile.innerHTML =
            '<img src="' + (p.image || placeholderImage) + '" alt="">' +
            '<div class="name">' + p.name + '</div>' +
            '<div class="price">' + formatMoney(p.price) + '</div>' +
            '<small class="text-muted">Stock: ' + p.stock + '</small>';
          tile.addEventListener('click', function () { addToCart(p.id, 1); });
          productGrid.appendChild(tile);
        });
      }

      if (barcodeInput) {
        barcodeInput.addEventListener('input', function () {
          var q = barcodeInput.value.trim().toLowerCase();
          if (!q) {
            searchResults.classList.add('d-none');
            searchResults.innerHTML = '';
            return;
          }
          var matches = products.filter(function (p) {
            return p.name.toLowerCase().includes(q) || p.barcode.toLowerCase().includes(q);
          }).slice(0, 6);
          searchResults.innerHTML = '';
          matches.forEach(function (p) {
            var a = document.createElement('button');
            a.type = 'button';
            a.className = 'list-group-item list-group-item-action';
            a.textContent = p.name + ' — ' + formatMoney(p.price) + ' (Stock: ' + p.stock + ')';
            a.addEventListener('click', function () {
              addToCart(p.id, 1);
              barcodeInput.value = '';
              searchResults.classList.add('d-none');
            });
            searchResults.appendChild(a);
          });
          searchResults.classList.toggle('d-none', matches.length === 0);
        });
      }

      [discountEl, taxEl, amountPaidEl].forEach(function (el) {
        if (el) el.addEventListener('input', renderCart);
      });

      if (clearBtn) {
        clearBtn.addEventListener('click', function () {
          cart = {};
          if (stockAlert) stockAlert.classList.add('d-none');
          renderCart();
        });
      }

      if (form) {
        form.addEventListener('submit', function (e) {
          var container = document.getElementById('posHiddenFields');
          container.innerHTML = '';
          var items = cartItems();
          if (!items.length) {
            e.preventDefault();
            return;
          }
          items.forEach(function (item) {
            var prodInput = document.createElement('input');
            prodInput.type = 'hidden';
            prodInput.name = 'products';
            prodInput.value = item.product.id;
            container.appendChild(prodInput);

            var qtyInput = document.createElement('input');
            qtyInput.type = 'hidden';
            qtyInput.name = 'quantity_' + item.product.id;
            qtyInput.value = item.qty;
            container.appendChild(qtyInput);
          });
        });
      }

      renderCart();
    },
  };
})();
