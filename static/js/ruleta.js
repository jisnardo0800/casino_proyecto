// static/js/ruleta.js
"use strict";

// ——————————————
// Configuración e inicialización
// ——————————————
const NUM_RED = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);

const balanceSp = document.getElementById("balance");
let balance     = Number(balanceSp.textContent) || 0;

const betSp      = document.getElementById("current-bet");
const resultSq   = document.getElementById("result-square");
const chips      = document.querySelectorAll(".chip");
const btnClear   = document.getElementById("clear-chip");
const btnSpin    = document.getElementById("spin-btn");
const table      = document.getElementById("table-container");
const topOut     = document.getElementById("outside-top");
const botOut     = document.getElementById("outside-bottom");

let selectedChip = 0;
let bets         = [];

// Actualiza Saldo y Apuesta en pantalla
function updateInfo() {
  balanceSp.textContent = balance;
  betSp.textContent     = bets.reduce((s,b)=> s + b.amount, 0);
}

// ——————————————
// Construye el tablero de ruleta
// ——————————————
;(function buildTable(){
  // Cero
  const zero = document.createElement("div");
  zero.className   = "bet-cell green zero-cell";
  zero.dataset.key = "0";
  zero.textContent = "0";
  zero.addEventListener("click", ()=> placeBet(zero));
  table.appendChild(zero);

  // Filas de números + “2 to 1”
  const rows = [
    [3,6,9,12,15,18,21,24,27,30,33,36],
    [2,5,8,11,14,17,20,23,26,29,32,35],
    [1,4,7,10,13,16,19,22,25,28,31,34]
  ];
  rows.forEach(fila => {
    fila.forEach(num => {
      const cell = document.createElement("div");
      cell.className   = "bet-cell " + (NUM_RED.has(num) ? "red" : "black");
      cell.dataset.key = String(num);
      cell.textContent = num;
      cell.addEventListener("click", ()=> placeBet(cell));
      table.appendChild(cell);
    });
    const side = document.createElement("div");
    side.className   = "bet-cell side-cell";
    side.dataset.key = "2to1";
    side.textContent = "2 to 1";
    side.addEventListener("click", ()=> placeBet(side));
    table.appendChild(side);
  });
})();

// Docenas
["1 to 12","13 to 24","25 to 36"].forEach(txt => {
  const d = document.createElement("div");
  d.className   = "outside";
  d.dataset.key = txt;
  d.textContent = txt;
  d.addEventListener("click", ()=> placeBet(d));
  topOut.appendChild(d);
});

// Even / Red / Black / Odd
["even","red","black","odd"].forEach(txt => {
  const d = document.createElement("div");
  d.className   = "outside";
  d.dataset.key = txt;
  d.textContent = txt.toUpperCase();
  d.addEventListener("click", ()=> placeBet(d));
  botOut.appendChild(d);
});

// ——————————————
// Selección de ficha
// ——————————————
chips.forEach(chip => {
  chip.addEventListener("click", () => {
    chips.forEach(c=>c.classList.remove("selected"));
    chip.classList.add("selected");
    selectedChip = Number(chip.dataset.value);
  });
});

// ——————————————
// Limpiar apuestas
// ——————————————
btnClear.addEventListener("click", () => {
  bets = [];
  selectedChip = 0;
  chips.forEach(c=>c.classList.remove("selected"));
  document.querySelectorAll(".chip-token").forEach(t=>t.remove());
  updateInfo();
});

// ——————————————
// Colocar o acumular apuesta
// ——————————————
function placeBet(el) {
  if (!selectedChip) {
    return alert("Elige una ficha primero");
  }
  const key = el.dataset.key;
  let bet = bets.find(x=> x.key === key);
  if (bet) {
    bet.amount += selectedChip;
  } else {
    bet = { key, amount: selectedChip };
    bets.push(bet);
  }
  // Si es un número, muestro token con cantidad
  if (/^\d+$/.test(key)) {
    let tok = el.querySelector(".chip-token");
    if (tok) {
      tok.textContent = bet.amount;
    } else {
      tok = document.createElement("div");
      tok.className   = "chip-token";
      tok.textContent = bet.amount;
      el.appendChild(tok);
    }
  }
  updateInfo();
}

// ——————————————
// Spin: lógica completa en JS (sin backend)
// ——————————————
btnSpin.addEventListener("click", () => {
  if (!bets.length) {
    resultSq.textContent = "Coloca una apuesta";
    return;
  }

  const totalBet = bets.reduce((s,b)=> s + b.amount, 0);
  if (balance < totalBet) {
    resultSq.textContent = "Saldo insuficiente";
    return;
  }

  // Genero número aleatorio 0–36
  const result = Math.floor(Math.random() * 37);

  // Calculo el payout total
  let payout = 0;
  bets.forEach(b => {
    const { key, amount } = b;

    // Pleno (número exacto paga x36 => neto +35)
    if (/^\d+$/.test(key) && Number(key) === result) {
      payout += amount * 36;
    }
    // Rojo/Negro
    else if (key === "red" && NUM_RED.has(result)) {
      payout += amount * 2;
    }
    else if (key === "black" && result !== 0 && !NUM_RED.has(result)) {
      payout += amount * 2;
    }
    // Par/Impar
    else if (key === "even" && result !== 0 && result % 2 === 0) {
      payout += amount * 2;
    }
    else if (key === "odd" && result % 2 === 1) {
      payout += amount * 2;
    }
    // Docenas (paga x3)
    else if (key === "1 to 12" && result >= 1 && result <= 12) {
      payout += amount * 3;
    }
    else if (key === "13 to 24" && result >= 13 && result <= 24) {
      payout += amount * 3;
    }
    else if (key === "25 to 36" && result >= 25 && result <= 36) {
      payout += amount * 3;
    }
    // Columnas “2 to 1” (paga x3)
    else if (key === "2to1") {
      payout += amount * 3;
    }
  });

  // Actualizo saldo: resto todo lo apostado y sumo el payout
  balance = balance - totalBet + payout;
  updateInfo();

  // Muestro el resultado y hago highlight
  resultSq.textContent = `Número ganador: ${result}`;
  const winner = document.querySelector(`.bet-cell[data-key="${result}"]`);
  if (winner) {
    winner.style.boxShadow = "0 0 15px 5px yellow";
    setTimeout(() => { winner.style.boxShadow = ""; }, 3000);
  }

  // Limpio para la siguiente ronda
  bets = [];
  selectedChip = 0;
  chips.forEach(c=>c.classList.remove("selected"));
  document.querySelectorAll(".chip-token").forEach(t=>t.remove());
});
// ——————————————