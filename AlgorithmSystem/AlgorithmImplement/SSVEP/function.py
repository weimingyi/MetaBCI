import numpy as np
from scipy.signal import lfilter, lfilter_zi
import scipy.linalg as scl
from numba import njit, prange


def horizontal_expanse_to_tense(x, order):
    n = x.shape
    if np.mod(n[1], order):
        print('error(维度不匹配)')
    y = x.reshape(n[0], int(n[1] / order), int(order), order="F")
    return y


def tense_horizontal_expanse(x):
    n = x.shape
    y = x.reshape(n[0], n[1] * n[2], order='F')
    return y


def arord(R, m, mcor, ne, pmin, pmax):
    imax = pmax - pmin

    sbc = np.zeros((1, imax + 1))
    fpe = np.zeros((1, imax + 1))
    logdp = np.zeros((1, imax + 1))
    np_m = np.zeros((1, imax + 1))

    np_m[0, imax] = m * pmax + mcor

    R22 = R[int(np_m[0, imax]):int(np_m[0, imax]) + m, int(np_m[0, imax]):int(np_m[0, imax]) + m]

    invR22 = np.linalg.inv(R22)
    Mp = np.dot(invR22, invR22.T)

    logdp[0, imax] = 2 * np.log(np.abs(np.prod(np.diag(R22))))

    i = imax
    for p in range(pmax, pmin - 1, -1):
        np_m[0, i] = m * p + mcor
        if p < pmax:
            Rp = R[int(np_m[0, i]):int(np_m[0, i]) + m, int(np_m[0, imax]):int(np_m[0, imax]) + m]
            L = np.linalg.cholesky(np.identity(m) + np.dot(np.dot(Rp, Mp), Rp.T)).T
            N = np.dot(np.linalg.inv(L.T), np.dot(Rp, Mp))  # !!!!!!!!!!!!!!!!!
            Mp = Mp - np.dot(N.T, N)
            logdp[0, i] = logdp[0, i + 1] + 2 * np.log(np.abs(np.prod(np.diag(L))))

        sbc[0, i] = logdp[0, i] / m - np.log(ne) * (ne - np_m[0, i]) / ne

        fpe[0, i] = logdp[0, i] / m - np.log(ne * (ne - np_m[0, i]) / (ne + np_m[0, i]))

        i = i - 1

    return sbc, fpe, logdp, np_m


def arqr(v, p, mcor):
    n, m = v.shape

    ne = n - p
    np_m = m * p + mcor
    K = np.zeros((ne, np_m + m))
    if mcor == 1:
        K[:, 0] = np.ones((ne, 1))

    for j in range(1, p + 1):
        K[:, mcor + m * (j - 1):mcor + m * j] = v[p - j:n - j, :]

    K[:, np_m:np_m + m] = v[p:n, :]
    q = np_m + m
    delta = (q ** 2 + q + 1) * np.finfo(np.float64).eps  # !!!!!!!!!!!
    scale = np.sqrt(delta) * np.sqrt(np.sum(np.power(K, 2), axis=0))

    Q, R = np.linalg.qr(np.vstack((K, np.diag(scale))))
    # Q, R = np.linalg.qr(np.vstack((K, np.diag(np.array(scale).squeeze()))), mode='complete')
    R = np.triu(R)

    return R, scale


def arfit(v, pmin, pmax, selector, no_const):
    n, m = v.shape
    if type(pmin) is not int or type(pmax) is not int:
        print("error: Order must be integer.")
    if pmax < pmin:
        print("error: PMAX must be greater than or equal to PMIN.")
    if selector is None:
        mcor = 1
        selector = 'sbc'
    elif no_const is None:
        if selector == 'zero':
            mcor = 0
            selector = 'sbc'
        else:
            mcor = 1
    else:
        if no_const == 'zero':
            mcor = 0
        else:
            print("error: Bad argument. Usage:  [w,A,C,SBC,FPE,th]=AR(v,pmin,pmax,SELECTOR,''zero'')")

    ne = n - pmax
    npmax = m * pmax + mcor

    if ne <= npmax:
        print("Time series too short.")
    R, scale = arqr(v, pmax, mcor)
    sbc, fpe, logdp, notuse = arord(R, m, mcor, ne, pmin, pmax)
    val = eval(selector).min(0)
    iopt = np.argmin(eval(selector))
    popt = pmin + iopt  # !!!!!!!!!!
    np_m = m * popt + mcor  # !!!!!!!!!!!
    R11 = R[0:np_m, 0:np_m]
    R12 = R[0:np_m, npmax:npmax + m]
    R22 = R[np_m:npmax + m, npmax:npmax + m]
    if np_m > 0:
        if mcor == 1:
            con = scale[1:npmax + m] / scale[0]  # !!!!!!!!!!
            R11[:, 0] = np.dot(R11[:, 0], con)
        Aaug = np.dot(np.linalg.inv(R11), R12).T
        if mcor == 1:
            w = np.dot(Aaug[:, 0], con)
            A = Aaug[:, 1:np_m]
        else:
            w = np.zeros((m, 1))
            A = Aaug  # np.zeros((0, 0))
    else:
        w = np.zeros((m, 1))
        A = np.zeros((0, 0))
    dof = ne - np_m
    C = np.dot(R22.T, R22) / dof
    invR11 = np.linalg.inv(R11)
    if mcor == 1:
        invR11[0, :] = np.dot(invR11[0, :], con)
    Uinv = np.dot(invR11, invR11.T)
    # th = np.hstack((np.array(dof), np.zeros((1, Uinv.shape[1] - 1))))
    th = np.vstack((np.zeros((1, Uinv.shape[1])), Uinv))
    th[0, 0] = dof
    return w, A, C, sbc, fpe, th


def EstimateSTEqualizer(data, P):
    if P is None:
        P = [4, 6]
    elif len(P) < 2:
        P[1] = P[0]

    # 去均值
    data = data - np.reshape(np.mean(data, 1), [data.shape[0], 1])

    STEqualizerTemp, STEDataD, V, armodel, C = equalizer_estimate(data, P)

    equalizerOrder = STEqualizerTemp.shape[2]
    STEqualizer = horizontal_expanse_to_tense(
        np.dot(np.diag((1 / np.sqrt(STEDataD)).reshape(STEDataD.shape[0])), tense_horizontal_expanse(
            STEqualizerTemp)), equalizerOrder)
    Pi = np.ceil((STEqualizer.shape[2]) / 2)
    return STEqualizer, Pi


def equalizer_estimate(x, P):
    L = x.shape[0]

    w, A, C, sbc, fpe, th = arfit(x.T, P[0], P[1], 'fpe', 'zero')

    armodel = np.hstack((np.identity(L), -A))
    [D, V] = np.linalg.eigh(C)

    V = -V
    V[:, 3] = -V[:, 3]
    D = D.reshape(len(D), 1)
    equalizerTense = np.dot(V.T, armodel)

    temp = horizontal_expanse_to_tense(equalizerTense, equalizerTense.shape[1] / L)
    # equalizer = np.zeros((temp.shape[0], temp.shape[1], 1))
    # for i in range(0, temp.shape[0]):
    #    for j in range(0, temp.shape[1]):
    #       equalizer =

    equalizer = temp

    return equalizer, D, V, armodel, C


def firfilter_matrix(filter_cell_matrix, input_data, zi=None):
    mo, mi = filter_cell_matrix.shape[0:2]
    if mi != input_data.shape[0]:
        print('error([输入数据与线性系统输入维度不同，线性相位系统维度:', mi, '输入数据维度', input_data.shape[0], ']')

    Zf = np.zeros((mo, mi, filter_cell_matrix.shape[2] - 1))
    output_data = np.zeros((mo, input_data.shape[1]))
    temp_data = np.zeros((mi, input_data.shape[1]))
    for i in range(mo - 1, -1, -1):
        for j in range(mi - 1, -1, -1):
            if zi is not None:

                temp_data[j, :], Zf[i, j, :] = lfilter(filter_cell_matrix[i, j, :], np.array([1]), input_data[j, :],
                                                       zi=zi[i, j])
            else:
                temp_data[j, :], Zf[i, j, :] = lfilter(filter_cell_matrix[i, j, :], np.array([1]), input_data[j, :],
                                        zi=lfilter_zi(filter_cell_matrix[i, j, :], np.array([1])) * input_data[j, 0])
                                                        # zi=np.ones((filter_cell_matrix.shape[2] - 1,)))
        output_data[i, :] = temp_data.sum(0)
    return output_data, Zf


def iterate_qr(r, new_data):
    if r is None:
        g1_size = 0
        r = new_data.T
    else:
        g1_size = r.shape[0]
        r = np.vstack((r, new_data.T))
    #     G,r_new = np.linalg.qr(R, mode='reduced')
    G, r_new, e = scl.qr(r, mode='economic', pivoting=True)  # !!!!!!!!!!
    # matlabQR分解会重排矩阵，还原重排结果
    E = np.identity(r_new.shape[1])
    r_new = np.dot(r_new, E[e])
    if g1_size == 0:
        g1 = np.zeros((new_data.shape[0], new_data.shape[0]))
    else:
        g1 = G[0:g1_size, :]
    g2 = G[g1_size:, :]
    return r_new, g1, g2


@njit(parallel=True)
def update_inner_product(cell, max_window_index, x_g1, x_g2, t_g1, t_g2):
    """
    原地更新内积，不返回值
    :param cell: 待更新的内积数组
    :param max_window_index:
    :param x_g1:
    :param x_g2:
    :param t_g1:
    :param t_g2:
    :return: None
    """
    for i in prange(t_g1.shape[0]):
        for j in range(max_window_index - 1, 0, -1):
            cell[i, j] = np.dot(np.dot(x_g1.T, cell[i, j - 1]), t_g1[i, j]) + np.dot(x_g2.T, t_g2[i, j])
        cell[i, 0] = np.dot(x_g2.T, t_g2[i, 0])


@njit(parallel=True)
def get_result(cell, max_window, step):
    noise_energy_matrix = np.zeros((cell.shape[0], max_window))
    signal_energy_cell = np.zeros((cell.shape[0], max_window))
    snr = np.zeros((cell.shape[0], max_window))
    for i in prange(cell.shape[0]):
        for j in prange(max_window):
            temp = np.dot(cell[i, j], cell[i, j].T)
            eigenvalues = np.linalg.eigvals(temp)
            s = np.sort(eigenvalues)
            noise_energy_matrix[i, j] = (temp.shape[0] - eigenvalues.sum()) * step * (j + 1)
            snr[i, j] = eigenvalues.sum() / (temp.shape[0] - eigenvalues.sum())
            signal_energy_cell[i, j] = 1.25 * s[-1] + 0.67 * s[-2] + 0.5 * s[-3]

    return noise_energy_matrix, signal_energy_cell, snr


@njit()
def numba_qr(a):
    return np.linalg.qr(a)
