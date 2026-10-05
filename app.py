from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)

DATABASE = "living_hard_drive.db"


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dna_sequence TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# =========================================================
# ENCODE DATA → DNA
# =========================================================

def encode_data(data):

    data_bytes = data.encode("utf-8")

    binary_data = ""

    for byte in data_bytes:
        binary_data += format(byte, "08b")

    dna_map = {
        "00": "A",
        "01": "C",
        "10": "G",
        "11": "T"
    }

    dna_sequence = ""

    for i in range(0, len(binary_data), 2):

        two_bits = binary_data[i:i + 2]

        dna_sequence += dna_map[two_bits]

    return dna_sequence


# =========================================================
# DECODE DNA → DATA
# =========================================================

def decode_data(dna_sequence):

    dna_sequence = dna_sequence.strip().upper()

    if not dna_sequence:
        return ""

    if any(base not in "ACGT" for base in dna_sequence):
        raise ValueError(
            "DNA sequence can contain only A, C, G and T."
        )

    dna_map = {
        "A": "00",
        "C": "01",
        "G": "10",
        "T": "11"
    }

    binary_data = ""

    for base in dna_sequence:

        binary_data += dna_map[base]

    data_bytes = bytearray()

    for i in range(0, len(binary_data), 8):

        byte = binary_data[i:i + 8]

        if len(byte) == 8:

            data_bytes.append(
                int(byte, 2)
            )

    try:

        return data_bytes.decode("utf-8")

    except UnicodeDecodeError:

        raise ValueError(
            "This DNA sequence could not be decoded correctly."
        )


# =========================================================
# STATISTICS
# =========================================================

def get_statistics(dna_sequence):

    dna_sequence = dna_sequence.upper()

    current_bases = len(dna_sequence)

    count_a = dna_sequence.count("A")
    count_c = dna_sequence.count("C")
    count_g = dna_sequence.count("G")
    count_t = dna_sequence.count("T")

    if current_bases > 0:

        gc_content = (
            (count_g + count_c)
            / current_bases
        ) * 100

        at_content = (
            (count_a + count_t)
            / current_bases
        ) * 100

    else:

        gc_content = 0
        at_content = 0

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM sequences"
    )

    saved_sequences = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(
            SUM(LENGTH(dna_sequence)), 0
        )
        FROM sequences
    """)

    total_bases = cursor.fetchone()[0]

    connection.close()

    return {
        "current_bases": current_bases,
        "saved_sequences": saved_sequences,
        "total_bases": total_bases,
        "a": count_a,
        "c": count_c,
        "g": count_g,
        "t": count_t,
        "gc": gc_content,
        "at": at_content
    }


# =========================================================
# HTML + CSS
# =========================================================

HTML = """

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>The Living Hard Drive</title>


<style>

/* ================= GENERAL ================= */

* {
    box-sizing: border-box;
}


body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #F4F7FB;

    color: #263238;
}


.container {

    width: 94%;

    max-width: 1400px;

    margin: auto;

    padding: 35px 0 50px;
}


/* ================= HEADER ================= */

.header {

    text-align: center;

    margin-bottom: 30px;
}


.header h1 {

    margin: 0;

    color: #17324D;

    font-size: 38px;

    font-weight: 700;
}


.header p {

    margin-top: 10px;

    color: #607D8B;

    font-size: 17px;
}


/* ================= LAYOUT ================= */

.main-layout {

    display: grid;

    grid-template-columns: 4fr 1fr;

    gap: 25px;

    align-items: start;
}


.left-column {

    display: flex;

    flex-direction: column;

    gap: 20px;
}


.right-column {

    display: flex;

    flex-direction: column;

    gap: 18px;
}


/* ================= CARD ================= */

.card {

    background: #FFFFFF;

    border-radius: 16px;

    padding: 25px;

    box-shadow:
        0 5px 20px rgba(0, 0, 0, 0.06);

    border: 1px solid #E7EDF3;
}


.card-title {

    font-size: 20px;

    font-weight: bold;

    color: #17324D;

    margin-bottom: 15px;
}


/* ================= TEXTAREA ================= */

textarea {

    width: 100%;

    border: 1px solid #D7E0E8;

    border-radius: 12px;

    padding: 15px;

    font-size: 15px;

    font-family: Arial, sans-serif;

    resize: vertical;

    outline: none;

    background: #FAFCFE;
}


textarea:focus {

    border-color: #2E7D6B;
}


.data-area {

    min-height: 220px;
}


.dna-area {

    min-height: 220px;

    background: #EAF6EE;

    font-family:
        "Courier New",
        monospace;

    letter-spacing: 1px;
}


/* ================= BUTTONS ================= */

.button-row {

    display: flex;

    gap: 12px;

    margin-top: 15px;

    flex-wrap: wrap;
}


button {

    border: none;

    border-radius: 10px;

    padding: 12px 20px;

    font-size: 15px;

    font-weight: bold;

    cursor: pointer;

    transition: 0.2s;
}


button:hover {

    transform: translateY(-1px);
}


.primary {

    background: #2E7D6B;

    color: white;
}


.primary:hover {

    background: #256856;
}


.secondary {

    background: #4A6FA5;

    color: white;
}


.secondary:hover {

    background: #3D5F8F;
}


.danger {

    background: #C94C4C;

    color: white;
}


.gray {

    background: #718096;

    color: white;
}


/* ================= DATABASE BUTTONS ================= */

.database-actions {

    display: flex;

    gap: 12px;

    flex-wrap: wrap;

    align-items: center;
}


.database-actions form {

    margin: 0;
}


.database-actions button {

    min-width: 160px;
}


/* ================= STATISTICS ================= */

.stats-grid {

    display: grid;

    grid-template-columns: 1fr 1fr;

    gap: 12px;
}


.stat {

    background: #F7F9FC;

    border-radius: 12px;

    padding: 15px;

    text-align: center;

    border: 1px solid #E8EDF3;
}


.stat-value {

    font-size: 23px;

    font-weight: bold;

    color: #2E7D6B;
}


.stat-label {

    font-size: 12px;

    color: #718096;

    margin-top: 5px;
}


/* ================= BASE COMPOSITION ================= */

.base-row {

    display: flex;

    justify-content: space-between;

    margin: 9px 0;

    font-family:
        "Courier New",
        monospace;

    font-weight: bold;
}


.progress {

    height: 7px;

    background: #E8EDF3;

    border-radius: 20px;

    overflow: hidden;

    margin-bottom: 12px;
}


.progress-inner {

    height: 100%;

    background: #2E7D6B;
}


/* ================= GC / AT ================= */

.gc-at-row {

    display: flex;

    justify-content: space-between;

    padding: 10px 0;

    font-weight: bold;

    border-bottom: 1px solid #EDF1F5;
}


.gc-at-row:last-child {

    border-bottom: none;
}


/* ================= SAVED ================= */

.saved-card {

    margin-top: 5px;
}


.sequence-box {

    background: #F7F9FC;

    border: 1px solid #E3EAF1;

    border-radius: 12px;

    padding: 15px;

    margin-bottom: 12px;
}


.sequence-id {

    font-weight: bold;

    color: #17324D;

    margin-bottom: 7px;
}


.sequence-text {

    font-family:
        "Courier New",
        monospace;

    word-break: break-all;

    color: #2E7D6B;

    font-size: 13px;
}


.sequence-actions {

    margin-top: 10px;

    display: flex;

    gap: 8px;
}


.small-button {

    padding: 8px 12px;

    font-size: 12px;
}


.empty {

    color: #718096;

    text-align: center;

    padding: 20px;
}


/* ================= RESPONSIVE ================= */

@media (max-width: 900px) {

    .main-layout {

        grid-template-columns: 1fr;
    }


    .header h1 {

        font-size: 30px;
    }
}


@media (max-width: 600px) {

    .container {

        width: 94%;

        padding-top: 20px;
    }


    .card {

        padding: 18px;
    }


    .database-actions {

        flex-direction: column;

        align-items: stretch;
    }


    .database-actions form {

        width: 100%;
    }


    .database-actions button {

        width: 100%;
    }


    .button-row {

        flex-direction: column;
    }


    .button-row button {

        width: 100%;
    }


    .stats-grid {

        grid-template-columns: 1fr 1fr;
    }
}

</style>

</head>


<body>


<div class="container">


    <!-- HEADER -->

    <div class="header">

        <h1>
            The Living Hard Drive
        </h1>

        <p>
            Store and retrieve data using DNA sequences
        </p>

    </div>


    <!-- MAIN -->

    <div class="main-layout">


        <!-- LEFT -->

        <div class="left-column">


            <!-- DATA -->

            <div class="card">

                <div class="card-title">
                    Data
                </div>


                <form method="POST"
                      action="/encode">


                    <textarea
                        class="data-area"
                        name="data"
                        placeholder="Enter your data here..."
                    >{{ data }}</textarea>


                    <div class="button-row">

                        <button
                            class="primary"
                            type="submit">

                            Encode to DNA

                        </button>

                    </div>


                </form>

            </div>


            <!-- DNA -->

            <div class="card">

                <div class="card-title">
                    DNA Sequence
                </div>


                <form method="POST"
                      action="/decode">


                    <textarea
                        class="dna-area"
                        name="dna"
                        placeholder="DNA sequence will appear here..."
                    >{{ dna }}</textarea>


                    <div class="button-row">

                        <button
                            class="secondary"
                            type="submit">

                            Decode

                        </button>

                    </div>


                </form>

            </div>


            <!-- DATABASE -->

            <div class="card">

                <div class="card-title">
                    Database
                </div>


                <div class="database-actions">


                    <!-- SAVE -->

                    <form method="POST"
                          action="/save">

                        <input
                            type="hidden"
                            name="dna"
                            value="{{ dna }}"
                        >

                        <button
                            class="primary"
                            type="submit">

                            Save to Database

                        </button>

                    </form>


                    <!-- LOAD -->

                    <form method="GET"
                          action="/saved">

                        <button
                            class="secondary"
                            type="submit">

                            Load Saved Data

                        </button>

                    </form>


                    <!-- CLEAR -->

                    <form method="GET"
                          action="/">

                        <button
                            class="gray"
                            type="submit">

                            Clear Screen

                        </button>

                    </form>


                </div>

            </div>


            <!-- SAVED SEQUENCES -->

            {% if saved_sequences is not none %}

            <div class="card saved-card">


                <div class="card-title">
                    Saved DNA Sequences
                </div>


                {% if saved_sequences %}


                    {% for sequence in saved_sequences %}


                    <div class="sequence-box">


                        <div class="sequence-id">

                            Sequence #{{ sequence["id"] }}

                        </div>


                        <div class="sequence-text">

                            {{ sequence["dna_sequence"] }}

                        </div>


                        <div class="sequence-actions">


                            <!-- LOAD DNA ONLY -->

                            <form method="POST"
                                  action="/load">

                                <input
                                    type="hidden"
                                    name="dna"
                                    value="{{ sequence['dna_sequence'] }}"
                                >

                                <button
                                    class="secondary small-button"
                                    type="submit">

                                    Load

                                </button>

                            </form>


                            <!-- DELETE -->

                            <form method="POST"
                                  action="/delete">

                                <input
                                    type="hidden"
                                    name="id"
                                    value="{{ sequence['id'] }}"
                                >

                                <button
                                    class="danger small-button"
                                    type="submit">

                                    Delete

                                </button>

                            </form>


                        </div>


                    </div>


                    {% endfor %}


                {% else %}


                    <div class="empty">

                        No saved DNA sequences yet.

                    </div>


                {% endif %}


            </div>

            {% endif %}


        </div>


        <!-- RIGHT -->

        <div class="right-column">


            <!-- STATISTICS -->

            <div class="card">

                <div class="card-title">
                    Statistics
                </div>


                <div class="stats-grid">


                    <div class="stat">

                        <div class="stat-value">

                            {{ stats["current_bases"] }}

                        </div>

                        <div class="stat-label">

                            Current Bases

                        </div>

                    </div>


                    <div class="stat">

                        <div class="stat-value">

                            {{ stats["saved_sequences"] }}

                        </div>

                        <div class="stat-label">

                            Saved Sequences

                        </div>

                    </div>


                    <div class="stat">

                        <div class="stat-value">

                            {{ stats["total_bases"] }}

                        </div>

                        <div class="stat-label">

                            Total Bases

                        </div>

                    </div>


                    <div class="stat">

                        <div class="stat-value">

                            DNA

                        </div>

                        <div class="stat-label">

                            Storage Type

                        </div>

                    </div>


                </div>

            </div>


            <!-- BASE COMPOSITION -->

            <div class="card">

                <div class="card-title">
                    Base Composition
                </div>


                <!-- A -->

                <div class="base-row">

                    <span>A</span>

                    <span>
                        {{ stats["a"] }}
                    </span>

                </div>


                <div class="progress">

                    <div
                        class="progress-inner"
                        style="width:
                        {{ (stats['a'] / stats['current_bases'] * 100)
                        if stats['current_bases'] else 0 }}%;">
                    </div>

                </div>


                <!-- C -->

                <div class="base-row">

                    <span>C</span>

                    <span>
                        {{ stats["c"] }}
                    </span>

                </div>


                <div class="progress">

                    <div
                        class="progress-inner"
                        style="width:
                        {{ (stats['c'] / stats['current_bases'] * 100)
                        if stats['current_bases'] else 0 }}%;">
                    </div>

                </div>


                <!-- G -->

                <div class="base-row">

                    <span>G</span>

                    <span>
                        {{ stats["g"] }}
                    </span>

                </div>


                <div class="progress">

                    <div
                        class="progress-inner"
                        style="width:
                        {{ (stats['g'] / stats['current_bases'] * 100)
                        if stats['current_bases'] else 0 }}%;">
                    </div>

                </div>


                <!-- T -->

                <div class="base-row">

                    <span>T</span>

                    <span>
                        {{ stats["t"] }}
                    </span>

                </div>


                <div class="progress">

                    <div
                        class="progress-inner"
                        style="width:
                        {{ (stats['t'] / stats['current_bases'] * 100)
                        if stats['current_bases'] else 0 }}%;">
                    </div>

                </div>


            </div>


            <!-- GC / AT -->

            <div class="card">

                <div class="card-title">
                    GC / AT Content
                </div>


                <div class="gc-at-row">

                    <span>
                        GC Content
                    </span>

                    <span>
                        {{ "%.1f"|format(stats["gc"]) }}%
                    </span>

                </div>


                <div class="gc-at-row">

                    <span>
                        AT Content
                    </span>

                    <span>
                        {{ "%.1f"|format(stats["at"]) }}%
                    </span>

                </div>


            </div>


        </div>


    </div>


</div>


</body>

</html>

"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    stats = get_statistics("")

    return render_template_string(

        HTML,

        data="",

        dna="",

        stats=stats,

        saved_sequences=None

    )


# =========================================================
# ENCODE
# =========================================================

@app.route("/encode", methods=["POST"])
def encode():

    data = request.form.get(
        "data",
        ""
    ).strip()


    if not data:

        stats = get_statistics("")

        return render_template_string(

            HTML,

            data="",

            dna="",

            stats=stats,

            saved_sequences=None

        )


    dna = encode_data(data)

    stats = get_statistics(dna)


    return render_template_string(

        HTML,

        data=data,

        dna=dna,

        stats=stats,

        saved_sequences=None

    )


# =========================================================
# DECODE
# =========================================================

@app.route("/decode", methods=["POST"])
def decode():

    dna = request.form.get(
        "dna",
        ""
    ).strip().upper()


    try:

        data = decode_data(dna)

    except ValueError as error:

        data = "Error: " + str(error)


    stats = get_statistics(dna)


    return render_template_string(

        HTML,

        data=data,

        dna=dna,

        stats=stats,

        saved_sequences=None

    )


# =========================================================
# SAVE
# =========================================================

@app.route("/save", methods=["POST"])
def save():

    dna = request.form.get(
        "dna",
        ""
    ).strip().upper()


    if dna:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(

            """
            INSERT INTO sequences (dna_sequence)
            VALUES (?)
            """,

            (dna,)

        )


        connection.commit()

        connection.close()


    return redirect(
        url_for("home")
    )


# =========================================================
# SHOW SAVED
# =========================================================

@app.route("/saved")
def saved():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        SELECT id, dna_sequence
        FROM sequences
        ORDER BY id DESC
        """

    )


    saved_sequences = cursor.fetchall()

    connection.close()


    stats = get_statistics("")


    return render_template_string(

        HTML,

        data="",

        dna="",

        stats=stats,

        saved_sequences=saved_sequences

    )


# =========================================================
# LOAD DNA ONLY
# =========================================================

@app.route("/load", methods=["POST"])
def load():

    dna = request.form.get(
        "dna",
        ""
    ).strip().upper()


    # IMPORTANT:
    # Load only puts DNA into the DNA box.
    # It does NOT decode automatically.

    stats = get_statistics(dna)


    return render_template_string(

        HTML,

        data="",

        dna=dna,

        stats=stats,

        saved_sequences=None

    )


# =========================================================
# DELETE
# =========================================================

@app.route("/delete", methods=["POST"])
def delete():

    sequence_id = request.form.get(
        "id"
    )


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        "DELETE FROM sequences WHERE id = ?",

        (sequence_id,)

    )


    connection.commit()

    connection.close()


    return redirect(
        url_for("saved")
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    init_database()

    app.run(
        debug=True
    )